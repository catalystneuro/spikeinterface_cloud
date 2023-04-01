// placeholders.ts
import { TableRowDataType } from "./types";

export const exampleData: TableRowDataType[] = [
    {
        id: 1,
        name: "Item 1",
        lastRun: "2021-10-01",
        status: "Success",
        data: { key: "value", anotherKey: "anotherValue" },
        logs: "Log message 1\nLog message 2\nLog message 3",
    },
    {
        id: 2,
        name: "Item 2",
        lastRun: "2021-10-05",
        status: "Failure",
        data: { foo: "bar", baz: "bat" },
        logs: "Error: Something happened\nWarning: Watch out\nInfo: Just FYI",
    },
];