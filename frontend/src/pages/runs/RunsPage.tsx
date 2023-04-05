import React from "react";
import { Container, Typography } from "@mui/material";
import { Box } from "@mui/material";
import RunsTable from "./RunsTable";


const RunsPage: React.FC = () => {
    return (
        <Box className="container">
            <Box component="form" className="form">
                <RunsTable />
            </Box>
        </Box>
    );
};

export default RunsPage;