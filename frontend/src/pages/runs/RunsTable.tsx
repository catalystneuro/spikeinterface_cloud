import React, { useState, useEffect } from "react";
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
import DeleteOutlinedIcon from '@material-ui/icons/DeleteOutlined';
import { makeStyles } from "@mui/styles";
import { TableRowDataType } from "./types";
import { exampleData } from "./placeholders"
import { restApiClient } from '../../services/clients/restapi.client';


const useStyles = makeStyles({
    table: {
        minWidth: 650,
    },
});

const RunsTable: React.FC = () => {
    const classes = useStyles();
    const [selectedRow, setSelectedRow] = useState<TableRowDataType | null>(null);
    const [tableData, setTableData] = useState<TableRowDataType[]>(exampleData);
    const [tabValue, setTabValue] = useState(0);

    // Fetch data from backend
    const fetchData = async () => {
        try {
            const response = await restApiClient.get('/runs/list');
            setTableData(response.data.runs);
        } catch (error) {
            console.error("Error fetching data:", error);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleSelectRow = (row: TableRowDataType): void => {
        setSelectedRow(row);
    };

    const handleDeleteRow = (index: number): void => {
        setTableData((prevData) => {
            const newData = [...prevData];
            newData.splice(index, 1);
            return newData;
        });
    };

    return (
        <>
            <TableContainer component={Paper}>
                <Table className={classes.table} sx={{ minWidth: 650 }} size="small">
                    <TableHead>
                        <TableRow>
                            <TableCell />
                            <TableCell>Description</TableCell>
                            <TableCell>Last run</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Delete</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {tableData.sort((a, b) => {
                            return new Date(b.lastRun).getTime() - new Date(a.lastRun).getTime();
                        }).map((row, index) => (
                            <TableRow key={row.identifier}>
                                <TableCell>
                                    <Radio
                                        checked={selectedRow?.identifier === row.identifier}
                                        onChange={() => handleSelectRow(row)}
                                    />
                                </TableCell>
                                <TableCell>{row.description}</TableCell>
                                <TableCell>{row.lastRun}</TableCell>
                                <TableCell
                                    style={{
                                        fontWeight: 'bold',
                                        color:
                                            row.status === 'running' ? 'blue' :
                                                row.status === 'success' ? 'green' :
                                                    row.status === 'fail' ? 'red' :
                                                        'inherit' // fallback color if none of the conditions match
                                    }}
                                >
                                    {row.status}
                                </TableCell>
                                <TableCell>
                                    <Button
                                        style={{ borderWidth: 0, color: "#3b3b3b" }}
                                        variant="outlined"
                                        startIcon={<DeleteOutlinedIcon />}
                                        onClick={() => handleDeleteRow(index)}
                                    >
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
                            value={JSON.stringify(selectedRow.metadata, null, 2)}
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