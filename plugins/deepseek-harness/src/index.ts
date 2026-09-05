import { spawn } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'
import z from '@deepseek-ai/schemastery'

export const name = 'nolane-memory'
export const inject = ['tools']

export interface Config {
  database?: string
  domain?: string
  principal?: string
  pythonExecutable?: string
  bridgePath?: string
  autoCreateDomain?: boolean
  enableReleaseGate?: boolean
  defaultTokenBudget?: number
  defaultPageFaultBudget?: number
  timeoutMs?: number
}

export const Config: z<Config> = z.object({
  database: z.string().default('nolane-memory.db'),
  domain: z.string().default('deepseek-harness'),
  principal: z.string().default('deepseek-agent'),
  pythonExecutable: z.string().default('python3'),
  bridgePath: z.string().default(''),
  autoCreateDomain: z.boolean().default(true),
  enableReleaseGate: z.boolean().default(false),
  defaultTokenBudget: z.number().default(4096),
  defaultPageFaultBudget: z.number().default(32),
  timeoutMs: z.number().default(30_000),
})

type ResolvedConfig = Required<Config>
type RpcResponse = { id: string; ok: true; result: unknown } | { id: string; ok: false; error: { type: string; message: string } }

function defaultBridgePath(): string {
  return fileURLToPath(new URL('../python/nolane_memory_bridge.py', import.meta.url))
}

function assertConfig(config: ResolvedConfig): void {
  if (!config.database.trim()) throw new Error('nolane-memory: database must not be empty')
  if (!config.domain.trim()) throw new Error('nolane-memory: domain must not be empty')
  if (!config.principal.trim()) throw new Error('nolane-memory: principal must not be empty')
  if (!config.pythonExecutable.trim()) throw new Error('nolane-memory: pythonExecutable must not be empty')
  if (!Number.isInteger(config.defaultTokenBudget) || config.defaultTokenBudget < 0) throw new Error('nolane-memory: defaultTokenBudget must be a non-negative integer')
  if (!Number.isInteger(config.defaultPageFaultBudget) || config.defaultPageFaultBudget < 0) throw new Error('nolane-memory: defaultPageFaultBudget must be a non-negative integer')
  if (!Number.isInteger(config.timeoutMs) || config.timeoutMs < 1) throw new Error('nolane-memory: timeoutMs must be a positive integer')
}

async function callBridge(config: ResolvedConfig, method: string, params: Record<string, unknown>): Promise<unknown> {
  const bridgePath = config.bridgePath || defaultBridgePath()
  const id = `dsh-${method}-${Date.now()}-${Math.random().toString(16).slice(2)}`
  const request = JSON.stringify({
    id,
    method,
    params: {
      ...params,
      db: config.database,
      domain: config.domain,
      principal: config.principal,
      auto_create_domain: config.autoCreateDomain,
    },
  })
  return await new Promise((resolve, reject) => {
    const child = spawn(config.pythonExecutable, [bridgePath], {
      stdio: ['pipe', 'pipe', 'pipe'],
      shell: false,
      env: process.env,
    })
    let stdout = ''
    let stderr = ''
    let settled = false
    const finish = (fn: () => void): void => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      fn()
    }
    const timer = setTimeout(() => {
      child.kill('SIGKILL')
      finish(() => reject(new Error(`nolane-memory bridge timed out after ${config.timeoutMs}ms`)))
    }, config.timeoutMs)
    child.stdout.on('data', chunk => { stdout += String(chunk) })
    child.stderr.on('data', chunk => { stderr += String(chunk) })
    child.on('error', error => finish(() => reject(error)))
    child.on('close', code => finish(() => {
      if (code !== 0) return reject(new Error(`nolane-memory bridge exited ${code}: ${stderr.trim()}`))
      const lines = stdout.split(/\r?\n/).filter(Boolean)
      const line = lines[0]
      if (lines.length !== 1 || line === undefined) return reject(new Error(`nolane-memory bridge protocol violation: expected one line, got ${lines.length}`))
      let response: RpcResponse
      try { response = JSON.parse(line) as RpcResponse }
      catch { return reject(new Error(`nolane-memory bridge returned invalid JSON: ${stdout.slice(0, 500)}`)) }
      if (response.id !== id) return reject(new Error('nolane-memory bridge response id mismatch'))
      if (!response.ok) return reject(new Error(`${response.error.type}: ${response.error.message}`))
      resolve(response.result)
    }))
    child.stdin.end(request + '\n')
  })
}

function jsonOutput() {
  return {
    schema: { type: 'string' as const },
    render: (_args: unknown, value: string) => [{ type: 'text' as const, text: value }],
  }
}

function asJson(value: unknown): string {
  return JSON.stringify(value)
}

export function apply(ctx: Context, config: Config): void {
  const resolved = config as ResolvedConfig
  assertConfig(resolved)

  ctx.tools.register(defineTool({
    name: 'nolane_memory_status',
    description: 'Inspect the configured Nolane Memory domain and semantic/research status without mutating memory.',
    parameters: {},
    output: jsonOutput(),
    async execute() { return asJson(await callBridge(resolved, 'status', {})) },
  }))

  ctx.tools.register(defineTool({
    name: 'nolane_memory_capture',
    description: 'Capture durable evidence. This does not self-promote model text into trusted factual authority.',
    parameters: {
      source_event_identity: { type: 'string', required: true, description: 'Stable semantic event identity; retries must reuse it.' },
      content_json: { type: 'string', required: true, description: 'JSON value to preserve as evidence.' },
      transport_channel: { type: 'string', description: 'Transport/channel label; defaults to deepseek-harness.' },
      external_identity: { type: 'string', description: 'External source identity when known.' },
      source_authority_class: { type: 'string', description: 'Explicit authority class; defaults to UNSPECIFIED.' },
      common_mode_group: { type: 'string', description: 'Common-mode failure group when known.' },
    },
    output: jsonOutput(),
    async execute(args) {
      let content: unknown
      try { content = JSON.parse(args.content_json) }
      catch { throw new Error('nolane_memory_capture: content_json must be valid JSON') }
      return asJson(await callBridge(resolved, 'capture', {
        source_event_identity: args.source_event_identity,
        content,
        transport_channel: args.transport_channel,
        external_identity: args.external_identity,
        source_authority_class: args.source_authority_class || 'UNSPECIFIED',
        common_mode_group: args.common_mode_group,
      }))
    },
  }))

  ctx.tools.register(defineTool({
    name: 'nolane_memory_recall',
    description: 'Compile an explicit Nolane Recall Frame from predeclared query-family and representation contracts.',
    parameters: {
      roles_json: { type: 'string', required: true, description: 'JSON array of RecallRole objects.' },
      token_budget: { type: 'number', description: 'Frame token budget.' },
      page_fault_budget: { type: 'number', description: 'Semantic page-fault budget.' },
      compatibility_profile_json: { type: 'string', description: 'Optional JSON object of applicability dimensions.' },
      safety_critical_dimensions_json: { type: 'string', description: 'Optional JSON array of safety-critical dimensions.' },
    },
    output: jsonOutput(),
    async execute(args) {
      let roles: unknown
      let compatibilityProfile: unknown = {}
      let safetyCriticalDimensions: unknown = []
      try {
        roles = JSON.parse(args.roles_json)
        if (args.compatibility_profile_json) compatibilityProfile = JSON.parse(args.compatibility_profile_json)
        if (args.safety_critical_dimensions_json) safetyCriticalDimensions = JSON.parse(args.safety_critical_dimensions_json)
      } catch { throw new Error('nolane_memory_recall: JSON arguments are invalid') }
      if (!Array.isArray(roles)) throw new Error('nolane_memory_recall: roles_json must be an array')
      if (typeof compatibilityProfile !== 'object' || compatibilityProfile === null || Array.isArray(compatibilityProfile)) throw new Error('nolane_memory_recall: compatibility_profile_json must be an object')
      if (!Array.isArray(safetyCriticalDimensions)) throw new Error('nolane_memory_recall: safety_critical_dimensions_json must be an array')
      return asJson(await callBridge(resolved, 'recall', {
        roles,
        token_budget: args.token_budget ?? resolved.defaultTokenBudget,
        page_fault_budget: args.page_fault_budget ?? resolved.defaultPageFaultBudget,
        compatibility_profile: compatibilityProfile,
        safety_critical_dimensions: safetyCriticalDimensions,
      }))
    },
  }))

  ctx.tools.register(defineTool({
    name: 'nolane_memory_verify',
    description: 'Verify canonical integrity, no-two-writable-clocks invariants, and full-spec ownership for the configured domain.',
    parameters: {},
    output: jsonOutput(),
    async execute() { return asJson(await callBridge(resolved, 'verify', {})) },
  }))

  if (resolved.enableReleaseGate) {
    ctx.tools.register(defineTool({
      name: 'nolane_memory_release_gate',
      description: 'Run the expensive Nolane Memory implementation release gate for diagnostics. Host must explicitly enable this tool.',
      parameters: {
        fuzz_cases: { type: 'number', description: 'Bounded state-model fuzz cases.' },
        differential_cases: { type: 'number', description: 'Independent-kernel differential cases.' },
      },
      output: jsonOutput(),
      async execute(args) {
        return asJson(await callBridge(resolved, 'release_gate', {
          fuzz_cases: args.fuzz_cases ?? 10_000,
          differential_cases: args.differential_cases ?? 128,
        }))
      },
    }))
  }
}
