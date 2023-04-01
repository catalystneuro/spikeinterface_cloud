import React from "react";
import { Container, Typography } from "@mui/material";
import RunsTable from "./RunsTable";

const RunsPage: React.FC = () => {
    return (
        <Container>
            <Typography variant="h4" component="h1" gutterBottom>
                Table Example
            </Typography>
            <RunsTable />
        </Container>
    );
};

export default RunsPage;