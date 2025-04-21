document.addEventListener('DOMContentLoaded', () => {
    // אלמנטים עיקריים
    const searchBtn = document.getElementById('search-btn');
    const domainInput = document.getElementById('domain');
    const companyInput = document.getElementById('company');
    const apiKeyInput = document.getElementById('api-key');
    const saveApiKeyBtn = document.getElementById('save-api-key');
    const clearHistoryBtn = document.getElementById('clear-history-btn');
    const loadingElem = document.getElementById('loading');
    const resultsElem = document.getElementById('results');
    const errorMessageElem = document.getElementById('error-message');
    const errorTextElem = document.getElementById('error-text');
    
    // ניווט
    const searchNav = document.getElementById('search-nav');
    const historyNav = document.getElementById('history-nav');
    const apiInfoNav = document.getElementById('api-info-nav');
    const searchSection = document.getElementById('search-section');
    const historySection = document.getElementById('history-section');
    const apiInfoSection = document.getElementById('api-info-section');
    
    // תבניות
    const emailItemTemplate = document.getElementById('email-item-template');
    const historyItemTemplate = document.getElementById('history-item-template');
    
    // אירועים
    searchBtn.addEventListener('click', handleSearch);
    saveApiKeyBtn.addEventListener('click', saveApiKey);
    clearHistoryBtn.addEventListener('click', clearHistory);
    
    // ניווט
    searchNav.addEventListener('click', (e) => {
        e.preventDefault();
        showSection(searchSection);
        setActiveNavLink(searchNav);
    });
    
    historyNav.addEventListener('click', (e) => {
        e.preventDefault();
        showSection(historySection);
        setActiveNavLink(historyNav);
        loadHistory();
    });
    
    apiInfoNav.addEventListener('click', (e) => {
        e.preventDefault();
        showSection(apiInfoSection);
        setActiveNavLink(apiInfoNav);
    });
    
    // פונקציית עזר - הצגת סקשן וההסתרת האחרים
    function showSection(section) {
        searchSection.classList.add('hidden');
        historySection.classList.add('hidden');
        apiInfoSection.classList.add('hidden');
        
        section.classList.remove('hidden');
    }
    
    // פונקציית עזר - הגדרת לינק פעיל בתפריט
    function setActiveNavLink(link) {
        searchNav.classList.remove('active');
        historyNav.classList.remove('active');
        apiInfoNav.classList.remove('active');
        
        link.classList.add('active');
    }
    
    // בעת טעינת הדף, טען את מפתח ה-API מהשרת (אם קיים)
    fetchApiKey();
    
    // פונקציה לטעינת מפתח ה-API מהשרת
    async function fetchApiKey() {
        try {
            const response = await fetch('/get-api-key');
            const data = await response.json();
            
            if (data.api_key) {
                apiKeyInput.value = data.api_key;
            }
        } catch (error) {
            console.error('שגיאה בטעינת מפתח API:', error);
        }
    }
    
    // פונקציה לשמירת מפתח ה-API
    async function saveApiKey() {
        const apiKey = apiKeyInput.value.trim();
        
        if (!apiKey) {
            showError('אנא הזן מפתח API תקין');
            return;
        }
        
        try {
            const response = await fetch('/save-api-key', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ api_key: apiKey })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showTemporaryMessage('מפתח API נשמר בהצלחה!', 'success');
            } else {
                showError(data.error || 'אירעה שגיאה בשמירת מפתח ה-API');
            }
        } catch (error) {
            showError('אירעה שגיאה בשמירת מפתח ה-API');
            console.error('Error saving API key:', error);
        }
    }
    
    // פונקציה להצגת הודעה זמנית
    function showTemporaryMessage(message, type = 'info') {
        const alertElem = document.createElement('div');
        alertElem.className = `alert alert-${type}`;
        alertElem.textContent = message;
        
        // הוספת ההודעה מעל שדה המפתח
        const apiKeySection = document.getElementById('api-key-section');
        apiKeySection.insertBefore(alertElem, apiKeySection.firstChild);
        
        // הסרת ההודעה אחרי 3 שניות
        setTimeout(() => {
            alertElem.remove();
        }, 3000);
    }
    
    // חיפוש באמצעות API
    async function handleSearch() {
        const domain = domainInput.value.trim();
        const company = companyInput.value.trim();
        const apiKey = apiKeyInput.value.trim();
        
        if (!domain) {
            showError('אנא הזן דומיין לחיפוש');
            domainInput.focus();
            return;
        }
        
        if (!apiKey) {
            showError('אנא הזן מפתח API מ-Hunter.io');
            apiKeyInput.focus();
            return;
        }
        
        try {
            // הצגת אנימציית טעינה
            loadingElem.classList.remove('hidden');
            resultsElem.classList.add('hidden');
            errorMessageElem.classList.add('hidden');
            
            // שליחת בקשה לשרת
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ domain, company, api_key: apiKey })
            });
            
            const data = await response.json();
            
            // הסתרת אנימציית טעינה
            loadingElem.classList.add('hidden');
            
            if (response.ok) {
                displayResults(data);
            } else {
                showError(data.error || 'אירעה שגיאה בעת ביצוע החיפוש');
            }
        } catch (error) {
            loadingElem.classList.add('hidden');
            showError('אירעה שגיאה בעת ביצוע החיפוש');
            console.error('Error during search:', error);
        }
    }
    
    // הצגת הודעת שגיאה
    function showError(message) {
        errorTextElem.textContent = message;
        errorMessageElem.classList.remove('hidden');
        
        // הסתרת ההודעה אחרי 5 שניות
        setTimeout(() => {
            errorMessageElem.classList.add('hidden');
        }, 5000);
    }
    
    // הצגת תוצאות החיפוש
    function displayResults(data) {
        if (!data.data) {
            showError('לא התקבלו תוצאות תקינות מהשרת');
            return;
        }
        
        const { domain, organization, emails, meta } = data.data;
        
        // הצגת מידע על הדומיין
        document.getElementById('result-domain').textContent = domain || '-';
        document.getElementById('result-organization').textContent = organization || '-';
        document.getElementById('result-total').textContent = meta ? meta.results : '0';
        
        // הצגת רשימת האימיילים
        const emailsList = document.getElementById('emails-list');
        emailsList.innerHTML = '';
        
        if (emails && emails.length > 0) {
            emails.forEach(email => {
                const emailItem = createEmailItem(email);
                emailsList.appendChild(emailItem);
            });
        } else {
            emailsList.innerHTML = '<p>לא נמצאו כתובות אימייל אמיתיות</p>';
        }
        
        // הצגת התוצאות
        resultsElem.classList.remove('hidden');
    }
    
    // יצירת פריט אימייל מתוך תבנית
    function createEmailItem(email) {
        const template = emailItemTemplate.content.cloneNode(true);
        
        // הצגת כתובת האימייל
        template.querySelector('.email-value').textContent = email.value || '-';
        
        // הצגת פרטי האדם אם קיימים
        if (email.first_name || email.last_name) {
            const name = `${email.first_name || ''} ${email.last_name || ''}`.trim();
            template.querySelector('.person-name').textContent = name;
        } else {
            template.querySelector('.person-name').textContent = 'לא ידוע';
        }
        
        // הצגת תפקיד אם קיים
        template.querySelector('.person-position').textContent = email.position || '';
        
        // הצגת ציון הביטחון
        const confidence = email.confidence || 0;
        template.querySelector('.confidence-level').style.width = `${confidence}%`;
        template.querySelector('.confidence-value').textContent = `${confidence}%`;
        
        return template;
    }
    
    // ניקוי היסטוריית חיפושים
    async function clearHistory() {
        try {
            const response = await fetch('/clear-history', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                // טעינת היסטוריה מחדש (שתהיה ריקה)
                loadHistory();
            }
        } catch (error) {
            console.error('Error clearing history:', error);
        }
    }
    
    // טעינת היסטוריית חיפושים
    async function loadHistory() {
        const historyList = document.getElementById('history-list');
        const loadingHistory = document.querySelector('.loading-history');
        
        try {
            loadingHistory.style.display = 'block';
            historyList.innerHTML = '';
            
            const response = await fetch('/history');
            const data = await response.json();
            
            loadingHistory.style.display = 'none';
            
            if (data.length === 0) {
                historyList.innerHTML = '<p>אין היסטוריית חיפושים</p>';
                return;
            }
            
            // הצגת ההיסטוריה
            data.forEach(item => {
                const historyItem = createHistoryItem(item);
                historyList.appendChild(historyItem);
            });
        } catch (error) {
            loadingHistory.style.display = 'none';
            historyList.innerHTML = '<p>אירעה שגיאה בטעינת ההיסטוריה</p>';
            console.error('Error loading history:', error);
        }
    }
    
    // יצירת פריט היסטוריה מתוך תבנית
    function createHistoryItem(item) {
        const template = historyItemTemplate.content.cloneNode(true);
        
        template.querySelector('.history-domain').textContent = item.domain;
        template.querySelector('.history-date').textContent = item.timestamp;
        template.querySelector('.history-company').textContent = item.company || 'ללא חברה';
        
        // הוספת אירוע לכפתור הצגת תוצאות
        const viewBtn = template.querySelector('.view-btn');
        viewBtn.addEventListener('click', () => {
            displayResults(item.results);
            
            // מעבר ללשונית החיפוש
            showSection(searchSection);
            setActiveNavLink(searchNav);
            
            // גלילה לתוצאות
            resultsElem.scrollIntoView({ behavior: 'smooth' });
        });
        
        return template;
    }
}); 