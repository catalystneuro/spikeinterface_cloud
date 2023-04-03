// placeholders.ts
import { TableRowDataType } from "./types";

export const exampleData: TableRowDataType[] = [
    {
        identifier: "abc",
        description: "Description 1",
        lastRun: "2021-10-01",
        status: "success",
        datasetName: "Dataset 1",
        metadata: { key: "value", anotherKey: "anotherValue" },
        logs: "Log message 1\nLog message 2\nLog message 3",
    },
    {
        identifier: "123",
        description: "description 2",
        lastRun: "2021-10-05",
        status: "fail",
        datasetName: "Dataset 2",
        metadata: { foo: "bar", baz: "bat" },
        logs: "Error: Something happened\nWarning: Watch out\nInfo: Just FYI",
    },
];