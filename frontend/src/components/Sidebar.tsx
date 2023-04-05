import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Box, List, ListItem, ListItemIcon, ListItemText } from '@mui/material';
import { Home, Settings, Logout, BarChart, History, QueryStats } from '@mui/icons-material';


interface NavItemProps {
    to: string;
    icon: React.ReactElement;
    text: string | React.ReactElement;
    disabled?: boolean;
}

const NavItem: React.FC<NavItemProps> = ({ to, icon, text, disabled = false }) => {
    const location = useLocation();
    const active = location.pathname === to;

    return (
        <ListItem button component={Link} to={to} selected={active} disabled={disabled}>
            <ListItemIcon style={{ color: active ? 'blue' : undefined }}>
                {icon}
            </ListItemIcon>
            <ListItemText primary={text} />
        </ListItem>
    );
};

const Sidebar: React.FC = () => {
    return (
        <Box sx={{ width: 240 }}>
            <List>
                <ListItem button component={Link} to={"/"}>
                    <ListItemIcon>
                        {<img src="/logo.png" alt="Logo" style={{ width: 40, height: 40 }} />}
                    </ListItemIcon>
                    <ListItemText primary={<span style={{ fontWeight: 'bold' }}>SpikeInterface</span>} />
                </ListItem>
                <NavItem
                    to="/datasets"
                    icon={<BarChart />}
                    text="Datasets"
                    disabled={true}
                />
                <NavItem
                    to="/sorting"
                    icon={<QueryStats />}
                    text="Spike Sorting"
                />
                <NavItem
                    to="/runs"
                    icon={<History />}
                    text="Runs"
                />
                <NavItem
                    to="/settings"
                    icon={<Settings />}
                    text="Settings"
                    disabled={true}
                />
                <NavItem
                    to="/logout"
                    icon={<Logout />}
                    text="Log out"
                    disabled={true}
                />
            </List>
        </Box>
    );
};

export default Sidebar;