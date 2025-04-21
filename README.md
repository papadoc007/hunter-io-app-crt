# Hunter.io חיפוש מידע

אפליקציה לחיפוש מידע באמצעות Hunter.io API עם ממשק משתמש גרפי ומערכת הרשאות.

## תכונות
- חיפוש כתובות אימייל לפי דומיין
- שמירת היסטוריית חיפושים
- מערכת התחברות והרשאות
- אימות דו-שלבי (2FA)
- הגבלת גישה לפי דומיין אימייל (crt-imp.com)
- ממשק ניהול משתמשים למנהלים
- תמיכה מלאה בעברית (RTL)

## טכנולוגיות
- **שרת:** Flask, SQLAlchemy, Flask-Login
- **לקוח:** HTML, CSS, JavaScript
- **אבטחה:** Werkzeug, PyOTP, אימות דו-שלבי
- **מסד נתונים:** SQLite (פיתוח), PostgreSQL (ייצור)

## התקנה והפעלה (מקומי)

### דרישות מקדימות
- Python 3.6+
- pip

### שלבים
1. התקן את החבילות הנדרשות:
   ```
   pip install -r requirements.txt
   ```

2. צור קובץ `.env` עם הגדרות סביבה:
   ```
   HUNTER_API_KEY=YOUR_API_KEY_HERE
   SECRET_KEY=your_secret_key_for_sessions
   ADMIN_EMAIL=admin@crt-imp.com
   ADMIN_PASSWORD=initial_admin_password
   ```

3. הפעל את האפליקציה:
   ```
   python app.py
   ```

4. גש לכתובת `http://localhost:5000` בדפדפן שלך

## דיפלוי ב-Vercel

1. התקן את Vercel CLI:
   ```
   npm install -g vercel
   ```

2. התחבר ל-Vercel:
   ```
   vercel login
   ```

3. הוסף את משתני הסביבה ב-Vercel:
   ```
   vercel secrets add hunter_api_key "YOUR_API_KEY_HERE"
   vercel secrets add secret_key "your_secret_key_for_sessions"
   vercel secrets add admin_email "admin@crt-imp.com"
   vercel secrets add admin_password "initial_admin_password"
   ```

4. בצע דיפלוי:
   ```
   vercel
   ```

## אבטחה

- האפליקציה מאובטחת עם מערכת התחברות ואימות
- רק משתמשים עם כתובות אימייל מדומיין crt-imp.com יכולים להירשם
- אימות דו-שלבי (2FA) זמין לכל המשתמשים
- הסיסמאות מאוחסנות בצורה מוצפנת במסד הנתונים

## הרשאות

- **משתמשים רגילים:** יכולים לבצע חיפושים ולצפות בהיסטוריית החיפושים שלהם
- **מנהלים:** יכולים לראות את כל המשתמשים ולנהל את המערכת

## הערות
- יש צורך במפתח API תקף של Hunter.io
- הנתונים נשמרים במסד נתונים SQLite בסביבת פיתוח ובמסד נתונים PostgreSQL בייצור

## רישיון
פרויקט זה הוא קוד פתוח ומופץ תחת רישיון MIT. 