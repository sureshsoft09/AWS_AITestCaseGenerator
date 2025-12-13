import React from 'react';
import { Box, CssBaseline } from '@mui/material';
import TopNavBar from './TopNavBar';

const Layout = ({ children }) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <CssBaseline />
      
      {/* Top Navigation */}
      <TopNavBar />
      
      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          mt: 8, // Account for top navigation
          background: 'linear-gradient(135deg, rgba(30, 58, 138, 0.05) 0%, rgba(241, 245, 249, 0.8) 25%, rgba(255, 255, 255, 0.9) 50%, rgba(226, 232, 240, 0.6) 75%, rgba(30, 58, 138, 0.03) 100%)',
          minHeight: 'calc(100vh - 64px)',
        }}
      >
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;