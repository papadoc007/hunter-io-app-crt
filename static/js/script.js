document.addEventListener('DOMContentLoaded', () => {
    // אלמנטים
    const searchBtn = document.getElementById('search-btn');
    const domainInput = document.getElementById('domain');
    const companyInput = document.getElementById('company');
    const loadingElem = document.getElementById('loading');
    const resultsElem = document.getElementById('results');
    const apiKeyErrorElem = document.getElementById('api-key-error');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // תבניות
    const emailItemTemplate = document.getElementById('email-item-template');
    const historyItemTemplate = document.getElementById('history-item-template');
    
    // אירועים
    searchBtn.addEventListener('click', handleSearch);
    
    // מעבר בין לשוניות
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            
            // הסרת הסימון מכל הלשוניות
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // הוספת סימון ללשונית הנוכחית
            btn.classList.add('active');
            document.getElementById(tabId).classList.add('active');
            
            // טעינת היסטוריה אם נלחץ על לשונית ההיסטוריה
            if (tabId === 'history-tab') {
                loadHistory();
            }
        });
    });
    
    // פונקציות
    
    // חיפוש באמצעות API
    async function handleSearch() {
        const domain = domainInput.value.trim();
        const company = companyInput.value.trim();
        
        if (!domain) {
            alert('אנא הזן דומיין לחיפוש');
            domainInput.focus();
            return;
        }
        
        try {
            // הצגת אנימציית טעינה
            loadingElem.classList.remove('hidden');
            resultsElem.classList.add('hidden');
            apiKeyErrorElem.classList.add('hidden');
            
            // שליחת בקשה לשרת
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ domain, company })
            });
            
            const data = await response.json();
            
            // הסתרת אנימציית טעינה
            loadingElem.classList.add('hidden');
            
            if (response.ok) {
                displayResults(data);
            } else {
                // בדיקה אם השגיאה היא בגלל מפתח API חסר
                if (data.error && data.error.includes('API')) {
                    apiKeyErrorElem.classList.remove('hidden');
                } else {
                    alert(`שגיאה: ${data.error || 'אירעה שגיאה בלתי צפויה'}`);
                }
            }
        } catch (error) {
            loadingElem.classList.add('hidden');
            alert('אירעה שגיאה בעת ביצוע החיפוש');
            console.error('Error during search:', error);
        }
    }
    
    // הצגת תוצאות החיפוש
    function displayResults(data) {
        if (!data.data) {
            alert('לא התקבלו תוצאות תקינות מהשרת');
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
            emailsList.innerHTML = '<p>לא נמצאו כתובות אימייל</p>';
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
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            document.querySelector('[data-tab="search-tab"]').classList.add('active');
            document.getElementById('search-tab').classList.add('active');
            
            // גלילה לתוצאות
            resultsElem.scrollIntoView({ behavior: 'smooth' });
        });
        
        return template;
    }
}); 