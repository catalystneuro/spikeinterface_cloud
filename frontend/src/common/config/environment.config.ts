
export type INodeEnv = 'development'
export type IApiEnv = 'local' | 'compose' | 'dev' | 'prod'

export interface IEnvironment {
    NODE_ENV: INodeEnv
    DEPLOY_MODE: IApiEnv
    USE_MOCK: boolean
}

/**
 * Stores all environment variables for easier access
 */
export const environment: IEnvironment = {
    NODE_ENV: process.env.NODE_ENV as INodeEnv,
    DEPLOY_MODE: process.env.DEPLOY_MODE as IApiEnv,
    USE_MOCK: !!process.env.REACT_APP_USE_MOCK
}
