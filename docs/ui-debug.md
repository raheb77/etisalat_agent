# UI Debug Checklist

This checklist is for manual validation of confidence labels, handoff banners, and localization in the CSR UI.

## Where to Set Locale
- In the main chat UI, use the **Locale** dropdown below the message textarea.
- Options: `ar-SA` and `en-US`.

## Sample Queries to Paste
Use these to generate predictable responses and verify UI behaviors:
- General: `What is the porting timeline for mobile numbers?`
- Billing: `What is the billing dispute window and response time?`
- Fraud/legal/security: `Report suspicious activity on my account.`

Note: If your backend supports hints or test fixtures, use those to force specific categories and confidence values.

## What to Check in ResponsePanel
- **Confidence** value and label in the response header.
- **Handoff** badge (`Yes`/`No`).
- **Reason** text (should not be generic confidence words in the wrong language).
- **Category** pill accent color (e.g., fraud/security should show red accent).
- **Citations** list (including evidence indicator and any expand/collapse behavior).

## Checklist
1. **65% confidence, `ar-SA` locale**
   - Badge label shows `ثقة متوسطة`.
   - Banner subtitle (if shown) uses `ثقة متوسطة` and is fully Arabic.
   - Reason field shows `ثقة متوسطة` (not an English phrase).

2. **20% confidence, `ar-SA` locale**
   - Badge label shows `ثقة منخفضة`.
   - If answer/citations are missing, fallback messaging remains in Arabic (no English strings).

3. **Fraud category, 50% confidence**
   - Banner is **forced** with red styling (more prominent than suggested).
   - Reason shows `تصنيف عالي الخطورة` in `ar-SA`.

4. **`en-US` locale**
   - Badge, banner subtitle, and reason are all English and consistent.
   - No Arabic strings appear in these fields.
