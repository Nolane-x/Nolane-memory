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
  type StringSpec = { type: 'string'; required?: true; description?: string }
  type NumberSpec = { type: 'number'; required?: true; description?: string }
  type BooleanSpec = { type: 'boolean'; required?: true; description?: string }
  type PropertySpec = StringSpec | NumberSpec | BooleanSpec
  type ParameterSchemaSpec = Record<string, PropertySpec>
  type ValueSchemaSpec = { type: 'string' } | { type: 'number' } | { type: 'boolean' } | { type: 'json' }
  type InferProperty<P> = P extends { type: 'string' } ? string : P extends { type: 'number' } ? number : P extends { type: 'boolean' } ? boolean : never
  type RequiredKeys<S> = { [K in keyof S]: S[K] extends { required: true } ? K : never }[keyof S]
  type InferArgs<S extends ParameterSchemaSpec> = {
    [K in RequiredKeys<S>]: InferProperty<S[K]>
  } & {
    [K in Exclude<keyof S, RequiredKeys<S>>]?: InferProperty<S[K]>
  }
  type InferOutput<O> = O extends { type: 'string' } ? string : O extends { type: 'number' } ? number : O extends { type: 'boolean' } ? boolean : unknown
  export function defineTool<const S extends ParameterSchemaSpec, const O extends ValueSchemaSpec>(definition: {
    name: string
    description: string
    parameters: S
    output: { schema: O; render: (args: InferArgs<S>, value: InferOutput<O>) => Array<{ type: 'text'; text: string }> }
    execute(args: InferArgs<S>, exec?: { signal: AbortSignal }): Promise<InferOutput<O>>
  }): unknown
}
