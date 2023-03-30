import React from 'react';
import { Link } from 'react-router-dom';
import { Box, List, ListItem, ListItemIcon, ListItemText } from '@mui/material';
import { Home, Settings, Logout, BarChart, History } from '@mui/icons-material';

const Sidebar: React.FC = () => {
    return (
        <Box sx={{ width: 240 }}>
            <List>
                <ListItem>
                    <ListItemIcon>
                        <Home />
                    </ListItemIcon>
                    <ListItemText primary="Logo" />
                </ListItem>
                <ListItem button component={Link} to="/datasets">
                    <ListItemIcon>
                        <BarChart />
                    </ListItemIcon>
                    <ListItemText primary="Datasets" />
                </ListItem>
                <ListItem button component={Link} to="/sorting">
                    <ListItemIcon>
                        <BarChart />
                    </ListItemIcon>
                    <ListItemText primary="Spike Sorting" />
                </ListItem>
                <ListItem button component={Link} to="/history">
                    <ListItemIcon>
                        <History />
                    </ListItemIcon>
                    <ListItemText primary="History" />
                </ListItem>
                <ListItem button component={Link} to="/settings">
                    <ListItemIcon>
                        <Settings />
                    </ListItemIcon>
                    <ListItemText primary="Settings" />
                </ListItem>
                <ListItem button>
                    <ListItemIcon>
                        <Logout />
                    </ListItemIcon>
                    <ListItemText primary="Log out" />
                </ListItem>
            </List>
        </Box>
    );
};

export default Sidebar;