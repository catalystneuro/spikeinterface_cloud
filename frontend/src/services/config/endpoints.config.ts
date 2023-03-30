import { environment, IApiEnv } from '../../common/config/environment.config'

interface IEndpoints {
    api: string
}

/**
 * Stores all endpoints accessed by the application
 */
const configEndpoints: Record<IApiEnv, IEndpoints> = {
    local: {
        api: 'http://localhost:8000/api'
    },
    compose: {
        api: 'http://localhost/api'
    },
    dev: {
        api: 'http://localhost/api'
    },
    prod: {
        api: 'http://localhost/api'
    }
}

/**
 * Exports all endpoints, already set up by current env
 */
export const endpoints = configEndpoints[environment.DEPLOY_MODE] ?? configEndpoints.local

export default endpoints