declare module 'node:child_process' {
  export interface ChildProcessWithoutNullStreams {
    stdin: { end(value?: string): void }
    stdout: { on(event: 'data', cb: (chunk: unknown) => void): void }
    stderr: { on(event: 'data', cb: (chunk: unknown) => void): void }
    on(event: 'error', cb: (error: Error) => void): void
    on(event: 'close', cb: (code: number | null) => void): void
    kill(signal?: string): boolean
  }
  export function spawn(command: string, args: string[], options: Record<string, unknown>): ChildProcessWithoutNullStreams
}
declare module 'node:url' { export function fileURLToPath(url: URL): string }
declare const process: { env: Record<string, string | undefined> }

declare module '@deepseek-ai/cordis' {
  export interface ToolRegistry { register(tool: unknown): void }
  export interface Context { tools: ToolRegistry }
}

declare module '@deepseek-ai/schemastery' {
  interface z<T = unknown> {
    default(value: unknown): z<T>
    min(value: number): z<T>
    max(value: number): z<T>
    description(value: string): z<T>
  }
  interface Factory {
    object<T>(shape: Record<string, unknown>): z<T>
    string(): z<string>
    number(): z<number>
    boolean(): z<boolean>
  }
  const z: Factory
  export default z
}

declare module '@deepseek-ai/dsh-tools' {
  export function defineTool(definition: {
    name: string
    description: string
    parameters: Record<string, unknown>
    output: { schema: unknown; render: (args: unknown, value: string) => Array<{ type: 'text'; text: string }> }
    execute(args: any): Promise<string>
  }): unknown
}
