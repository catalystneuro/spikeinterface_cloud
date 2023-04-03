export interface TableRowDataType {
    identifier: string;
    description: string;
    lastRun: string;
    status: 'running' | 'success' | 'fail';
    datasetName: string;
    metadata: Record<string, string>;
    logs: string;
}