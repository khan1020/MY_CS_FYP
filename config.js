/**
 * Centralized Backend API Configuration
 * 
 * Update the BACKEND_URL when your ngrok tunnel restarts or when deploying to production.
 * All frontend files will automatically use this URL.
 * 
 * Usage in HTML files:
 * <script src="config.js"></script>
 * <script>
 *   const BASE_URL = window.API_CONFIG.BACKEND_URL;
 *   // Now use BASE_URL for all API calls
 * </script>
 */

const API_CONFIG = {
    // Update this URL when ngrok restarts or for production deployment
    BACKEND_URL: 'https://e13febe3a5e1.ngrok-free.app',

    // API endpoints (for reference and easy changes)
    ENDPOINTS: {
        // Authentication
        LOGIN: '/login',
        REGISTER: '/register',
        VERIFY_OTP: '/verify_otp',
        RESEND_OTP: '/resend_otp',

        // Profile
        PROFILE: '/profile',
        PROFILE_PICTURE: '/profile/picture',
        PROFILE_PASSWORD: '/profile/password',

        // Chat
        ASK: '/ask',
        CHATS: '/chats',
        GET_MESSAGES: '/get_messages',
        DELETE_CHAT: '/delete_chat',

        // Files
        UPLOAD_FILE: '/upload_file',
        USER_PDFS: '/user_pdfs',

        // Voice
        UPLOAD_VOICE: '/upload_voice',
        VOICE_CHAT: '/voice_chat',

        // Enhanced RAG Features
        COUNT_WORDS: '/count_words',
        EXTRACT_KEYWORDS: '/extract_keywords',
        DOCUMENT_STATS: '/document_stats',
        QUERY_HISTORY: '/query_history',
        RERUN_QUERY: '/rerun_query',

        // Bookmarks & Templates
        BOOKMARKS: '/bookmarks',
        EXPORT_BOOKMARKS: '/export_bookmarks',
        TEMPLATES: '/templates',
        EXECUTE_TEMPLATE: '/execute_template',

        // Utilities
        HEALTH: '/health',
        SUPPORT: '/support',
        DOWNLOAD_DATA: '/download_data',
        DELETE_ACCOUNT: '/account'
    }
};

// Make config globally available
window.API_CONFIG = API_CONFIG;

// Helper function to build full URL
window.getApiUrl = function (endpoint) {
    return API_CONFIG.BACKEND_URL + endpoint;
};

console.log('✅ API Configuration loaded. Backend URL:', API_CONFIG.BACKEND_URL);
