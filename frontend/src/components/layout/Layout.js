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
          background: 'linear-gradient(180deg, #f8faff 0%, #ffffff 100%)',
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