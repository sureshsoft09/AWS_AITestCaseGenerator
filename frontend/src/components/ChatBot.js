import React, { useEffect, useRef } from 'react';

const ChatBot = () => {
  const messengerRef = useRef(null);
  const scriptLoadedRef = useRef(false);

  useEffect(() => {
    // Check if script is already loaded to prevent duplicate loading
    if (scriptLoadedRef.current || document.querySelector('script[src*="df-messenger.js"]')) {
      return;
    }

    // Load Dialogflow messenger CSS only if not already loaded
    if (!document.querySelector('link[href*="df-messenger-default.css"]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://www.gstatic.com/dialogflow-console/fast/df-messenger/prod/v1/themes/df-messenger-default.css';
      document.head.appendChild(link);
    }

    // Load Dialogflow messenger script with proper error handling
    const script = document.createElement('script');
    script.src = 'https://www.gstatic.com/dialogflow-console/fast/df-messenger/prod/v1/df-messenger.js';
    script.async = true;
    script.onload = () => {
      scriptLoadedRef.current = true;
      console.log('Dialogflow messenger script loaded successfully');
    };
    script.onerror = (error) => {
      console.error('Failed to load Dialogflow messenger script:', error);
    };
    document.head.appendChild(script);

    // Add custom styles with unique ID to prevent duplication
    if (!document.querySelector('#df-messenger-styles')) {
      const style = document.createElement('style');
      style.id = 'df-messenger-styles';
      style.textContent = `
        df-messenger {
          z-index: 999;
          position: fixed;
          --df-messenger-font-color: #000;
          --df-messenger-font-family: Google Sans;
          --df-messenger-chat-background: #f3f6fc;
          --df-messenger-message-user-background: #d3e3fd;
          --df-messenger-message-bot-background: #fff;
          bottom: 16px;
          right: 16px;
        }
      `;
      document.head.appendChild(style);
    }
  }, []);

  return (
    <div ref={messengerRef}>
      <df-messenger
        location="us"
        project-id="gen-lang-client-0182599221"
        agent-id="59d0e1ba-4c6d-4543-acdd-86b55e630a56"
        language-code="en"
        max-query-length="-1"
      >
        <df-messenger-chat-bubble
          chat-title="MedAssureAIAgent"
        >
        </df-messenger-chat-bubble>
      </df-messenger>
    </div>
  );
};

export default ChatBot;