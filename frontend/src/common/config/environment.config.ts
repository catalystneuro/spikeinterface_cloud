
export type INodeEnv = 'development'
export type IApiEnv = 'local' | 'compose' | 'dev' | 'prod'

export interface IEnvironment {
    NODE_ENV: INodeEnv
    DEPLOY_MODE: IApiEnv
    USE_MOCK: boolean
}


const global = (globalThis.process ?? import.meta)

/**
 * Stores all environment variables for easier access
 */
export const environment: IEnvironment = {
    NODE_ENV: global.env?.NODE_ENV as INodeEnv,
    DEPLOY_MODE: global.env?.DEPLOY_MODE as IApiEnv,
    USE_MOCK: !!global.env?.REACT_APP_USE_MOCK
}
