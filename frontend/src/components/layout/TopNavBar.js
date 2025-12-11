/* eslint-disable no-unused-vars */
import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Chip,
  Button,
  Tooltip,
} from '@mui/material';
import api from '../../services/api';
import {
  Dashboard as DashboardIcon,
  AutoAwesome as GenerateIcon,
  Tune as TuneIcon,
  MoveUp as MigrateIcon,
  Analytics as AnalyticsIcon,
  Notifications as NotificationsIcon,
  AccountCircle as AccountCircleIcon,
} from '@mui/icons-material';

const navigationItems = [
  {
    text: 'Dashboard',
    icon: <DashboardIcon />,
    path: '/dashboard',
  },
  {
    text: 'Generate',
    icon: <GenerateIcon />,
    path: '/generate',
  },
  {
    text: 'Enhance',
    icon: <TuneIcon />,
    path: '/enhance',
  },
  {
    text: 'Migrate',
    icon: <MigrateIcon />,
    path: '/migrate',
  },
  {
    text: 'Analytics',
    icon: <AnalyticsIcon />,
    path: '/analytics',
  },
];

const TopNavBar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleNavigation = (path) => {
    // Don't navigate if already on the same path
    if (location.pathname === path) {
      return;
    }

    // Navigate immediately
    navigate(path);
    
    // Reset agent session in background
    api.resetAgentSession()
      .then(() => {
        console.log('Agent session reset successfully');
      })
      .catch((error) => {
        console.error('Failed to reset agent session:', error);
      });
  };

  const isActivePath = (path) => {
    return location.pathname === path;
  };
  return (
    <AppBar
      position="fixed"
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 1,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between' }}>
        {/* Left side - Logo and Brand */}
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Box
            sx={{
              width: 40,
              height: 40,
              borderRadius: 2,
              background: 'rgba(255, 255, 255, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mr: 2,
              backdropFilter: 'blur(10px)',
            }}
          >
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                color: 'white',
                fontSize: '1.2rem',
              }}
            >
              M
            </Typography>
          </Box>
          
          <Typography
            variant="h6"
            noWrap
            component="div"
            sx={{
              fontWeight: 700,
              fontSize: '1.5rem',
              background: 'linear-gradient(45deg, #ffffff 30%, #f0f8ff 90%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              mr: 2,
            }}
          >
            MedAssureAI
          </Typography>
          
          <Chip
            label="AI-Powered"
            size="small"
            sx={{
              background: 'rgba(255, 255, 255, 0.2)',
              color: 'white',
              fontWeight: 500,
              backdropFilter: 'blur(10px)',
            }}
          />
        </Box>

        {/* Center - Navigation Items */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {navigationItems.map((item) => (
            <Tooltip key={item.path} title={item.text}>
              <Button
                onClick={() => handleNavigation(item.path)}
                startIcon={item.icon}
                sx={{
                  color: 'white',
                  minWidth: 'auto',
                  px: 2,
                  py: 1,
                  borderRadius: 2,
                  textTransform: 'none',
                  fontWeight: isActivePath(item.path) ? 600 : 400,
                  backgroundColor: isActivePath(item.path) ? 'rgba(255, 255, 255, 0.2)' : 'transparent',
                  backdropFilter: isActivePath(item.path) ? 'blur(10px)' : 'none',
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.15)',
                    backdropFilter: 'blur(10px)',
                    transform: 'translateY(-1px)',
                  },
                  transition: 'all 0.2s ease-in-out',
                  display: { xs: 'none', md: 'flex' }, // Hide on small screens
                }}
              >
                {item.text}
              </Button>
            </Tooltip>
          ))}
          
          {/* Mobile navigation - show icons only */}
          <Box sx={{ display: { xs: 'flex', md: 'none' }, gap: 0.5 }}>
            {navigationItems.map((item) => (
              <Tooltip key={item.path} title={item.text}>
                <IconButton
                  onClick={() => handleNavigation(item.path)}
                  sx={{
                    color: 'white',
                    backgroundColor: isActivePath(item.path) ? 'rgba(255, 255, 255, 0.2)' : 'transparent',
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 0.15)',
                    },
                  }}
                >
                  {item.icon}
                </IconButton>
              </Tooltip>
            ))}
          </Box>
        </Box>

        {/* Right side - User actions */}
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <IconButton 
            color="inherit"
            sx={{
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.15)',
              },
            }}
          >
            <NotificationsIcon />
          </IconButton>
          <IconButton 
            color="inherit"
            sx={{
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.15)',
              },
            }}
          >
            <AccountCircleIcon />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default TopNavBar;