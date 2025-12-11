import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Box,
  Divider,
  Typography,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  AutoAwesome as GenerateIcon,
  Tune as TuneIcon,
  MoveUp as MigrateIcon,
  Analytics as AnalyticsIcon,
  Science as AIIcon,
} from '@mui/icons-material';

const drawerWidth = 280;

const menuItems = [
  {
    text: 'Dashboard',
    icon: <DashboardIcon />,
    path: '/dashboard',
    description: 'Project overview & hierarchy',
  },
  {
    text: 'Test Case Generation',
    icon: <GenerateIcon />,
    path: '/generate',
    description: 'AI-powered test creation',
  },
  {
    text: 'Enhance Test Cases',
    icon: <TuneIcon />,
    path: '/enhance',
    description: 'Improve existing tests',
  },
  {
    text: 'Migration Test Cases',
    icon: <MigrateIcon />,
    path: '/migrate',
    description: 'Import legacy test data',
  },
  {
    text: 'Analytics Report',
    icon: <AnalyticsIcon />,
    path: '/analytics',
    description: 'Insights & reporting',
  },
];

const Sidebar = ({ open, onToggle }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleNavigation = (path) => {
    navigate(path);
  };

  return (
    <Drawer
      variant="persistent"
      anchor="left"
      open={open}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          background: 'linear-gradient(180deg, #ffffff 0%, #f8faff 100%)',
          borderRight: '1px solid rgba(102, 126, 234, 0.1)',
          mt: 8,
        },
      }}
    >
      <Box sx={{ p: 3 }}>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            p: 2,
            borderRadius: 2,
            background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
            mb: 2,
          }}
        >
          <AIIcon sx={{ color: '#667eea', mr: 1 }} />
          <Typography
            variant="subtitle2"
            sx={{
              fontWeight: 600,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            Healthcare Test Management
          </Typography>
        </Box>
      </Box>

      <Divider sx={{ borderColor: 'rgba(102, 126, 234, 0.1)' }} />

      <List sx={{ px: 2, py: 1 }}>
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          
          return (
            <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                onClick={() => handleNavigation(item.path)}
                sx={{
                  borderRadius: 2,
                  py: 1.5,
                  px: 2,
                  background: isActive
                    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                    : 'transparent',
                  color: isActive ? 'white' : 'inherit',
                  '&:hover': {
                    background: isActive
                      ? 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)'
                      : 'rgba(102, 126, 234, 0.08)',
                  },
                  transition: 'all 0.3s ease',
                }}
              >
                <ListItemIcon
                  sx={{
                    color: isActive ? 'white' : '#667eea',
                    minWidth: 40,
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <Box>
                  <ListItemText
                    primary={item.text}
                    primaryTypographyProps={{
                      fontWeight: isActive ? 600 : 500,
                      fontSize: '0.95rem',
                    }}
                  />
                  <Typography
                    variant="caption"
                    sx={{
                      color: isActive ? 'rgba(255, 255, 255, 0.7)' : 'text.secondary',
                      fontSize: '0.75rem',
                    }}
                  >
                    {item.description}
                  </Typography>
                </Box>
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      <Box sx={{ mt: 'auto', p: 2 }}>
        <Box
          sx={{
            p: 2,
            borderRadius: 2,
            background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)',
            border: '1px solid rgba(102, 126, 234, 0.1)',
          }}
        >
          <Typography variant="caption" color="text.secondary">
            💡 Powered by advanced AI agents for comprehensive healthcare test case management
          </Typography>
        </Box>
      </Box>
    </Drawer>
  );
};

export default Sidebar;