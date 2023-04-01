import React, { useState } from "react";
import {
    Box,
    Radio,
    TextField,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Button,
    Paper,
    Tabs,
    Tab,
} from "@mui/material";
import { makeStyles } from "@mui/styles";
import { TableRowDataType } from "./types";
import { exampleData } from "./placeholders"

const useStyles = makeStyles({
    table: {
        minWidth: 650,
    },
});

const RunsTable: React.FC = () => {
    const classes = useStyles();
    const [selectedRow, setSelectedRow] = useState<TableRowDataType | null>(null);
    const [placeholderData, setPlaceholderData] = useState(exampleData);
    const [tabValue, setTabValue] = useState(0);

    const handleSelectRow = (row: TableRowDataType): void => {
        setSelectedRow(row);
    };

    const handleDeleteRow = (index: number): void => {
        setPlaceholderData((prevData) => {
            const newData = [...prevData];
            newData.splice(index, 1);
            return newData;
        });
    };

    return (
        <>
            <TableContainer component={Paper}>
                <Table className={classes.table}>
                    <TableHead>
                        <TableRow>
                            <TableCell />
                            <TableCell>Name</TableCell>
                            <TableCell>Last run</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Delete</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {placeholderData.map((row, index) => (
                            <TableRow key={row.id}>
                                <TableCell>
                                    <Radio
                                        checked={selectedRow?.id === row.id}
                                        onChange={() => handleSelectRow(row)}
                                    />
                                </TableCell>
                                <TableCell>{row.name}</TableCell>
                                <TableCell>{row.lastRun}</TableCell>
                                <TableCell>{row.status}</TableCell>
                                <TableCell>
                                    <Button
                                        variant="contained"
                                        color="error"
                                        onClick={() => handleDeleteRow(index)}
                                    >
                                        Delete
                                    </Button>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>

            {selectedRow && (
                <Box>
                    <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
                        <Tab label="Data" />
                        <Tab label="Logs" />
                    </Tabs>
                    {tabValue === 0 ? (
                        <TextField
                            multiline
                            fullWidth
                            value={JSON.stringify(selectedRow.data, null, 2)}
                            InputProps={{
                                readOnly: true,
                            }}
                        />
                    ) : (
                        <TextField
                            multiline
                            fullWidth
                            value={selectedRow.logs}
                            InputProps={{
                                readOnly: true,
                            }}
                        />
                    )}
                </Box>
            )}
        </>
    );
};

export default RunsTable;