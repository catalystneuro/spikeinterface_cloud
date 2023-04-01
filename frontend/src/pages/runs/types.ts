export interface TableRowDataType {
    id: number;
    name: string;
    lastRun: string;
    status: string;
    data: Record<string, string>;
    logs: string;
}