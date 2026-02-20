/**
 * API layer — centralised fetch wrapper for all backend endpoints.
 * Uses the Vite proxy (/api → http://localhost:8000/api).
 */

const RAW_BASE = import.meta.env.VITE_API_BASE || '/api';
const BASE = RAW_BASE.replace(/\/+$/, '');

async function request(path, options = {}) {
    const res = await fetch(`${BASE}${path}`, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || `Request failed: ${res.status}`);
    }
    return res;
}

async function json(path, options) {
    const res = await request(path, options);
    return res.json();
}

// ── Upload ────────────────────────────────────────────────────────
export async function uploadFile(file) {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${BASE}/upload/file`, { method: 'POST', body: form });
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Upload failed');
    return res.json();
}

export async function confirmMapping(sessionId, mapping) {
    const form = new FormData();
    form.append('session_id', sessionId);
    form.append('mapping', JSON.stringify(mapping));
    const res = await fetch(`${BASE}/upload/confirm-mapping`, { method: 'POST', body: form });
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Mapping failed');
    return res.json();
}

export async function loadSample(name = 'school') {
    return json(`/upload/sample/${name}`);
}

export async function endUploadSession(sessionId = null) {
    const form = new FormData()
    if (sessionId) form.append('session_id', sessionId)
    const res = await fetch(`${BASE}/upload/end-session`, { method: 'POST', body: form })
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Failed to end session')
    return res.json()
}

export async function getSession(sessionId) {
    return json(`/upload/session/${sessionId}`);
}

// ── Cleaning ──────────────────────────────────────────────────────
export async function cleanPreview(data, options = {}) {
    return json('/clean/preview', {
        method: 'POST',
        body: JSON.stringify({ data, options }),
    });
}

export async function cleanApply(data, options = {}) {
    return json('/clean/apply', {
        method: 'POST',
        body: JSON.stringify({ data, options }),
    });
}

// ── Analytics ─────────────────────────────────────────────────────
export async function getOverview(data) {
    return json('/analyze/overview', {
        method: 'POST',
        body: JSON.stringify({ data }),
    });
}

export async function getSubjects(data) {
    return json('/analyze/subjects', {
        method: 'POST',
        body: JSON.stringify({ data }),
    });
}

export async function getRisk(data) {
    return json('/analyze/risk', {
        method: 'POST',
        body: JSON.stringify({ data }),
    });
}

export async function getGaps(data) {
    return json('/analyze/gaps', {
        method: 'POST',
        body: JSON.stringify({ data }),
    });
}

export async function getInsights(data) {
    return json('/analyze/insights', {
        method: 'POST',
        body: JSON.stringify({ data }),
    });
}

export async function getStudentProfile(studentId, data) {
    return json(`/analyze/student/${studentId}`, {
        method: 'POST',
        body: JSON.stringify({ data }),
    });
}

export async function getTermComparison(data) {
    return json('/analyze/term-comparison', {
        method: 'POST',
        body: JSON.stringify({ data }),
    });
}

export async function getSchoolModes() {
    return json('/analyze/school-modes');
}

// ── Reports (returns blob for download) ───────────────────────────
async function downloadBlob(path, body, filename) {
    const res = await request(path, {
        method: 'POST',
        body: JSON.stringify(body),
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

async function getBlobUrl(path, body) {
    const res = await request(path, {
        method: 'POST',
        body: JSON.stringify(body),
    });
    const blob = await res.blob();
    return URL.createObjectURL(blob);
}

export function downloadSchoolPdf(data) {
    return downloadBlob('/reports/school-pdf', { data }, 'EduMetrics_School_Report.pdf');
}

export function downloadClassPdf(data, className) {
    return downloadBlob('/reports/class-pdf', { data, class_name: className },
        `EduMetrics_Class_Performance_${className}.pdf`);
}

export function downloadStudentPdf(data, studentId) {
    return downloadBlob('/reports/student-pdf', { data, student_id: studentId },
        `EduMetrics_Student_${studentId}.pdf`);
}

export function downloadExcel(data) {
    return downloadBlob('/reports/excel', { data }, 'EduMetrics_Export.xlsx');
}

export async function openSchoolPdf(data) {
    const url = await getBlobUrl('/reports/school-pdf', { data });
    window.open(url, '_blank', 'noopener,noreferrer');
    return url;
}

export async function openClassPdf(data, className) {
    const url = await getBlobUrl('/reports/class-pdf', { data, class_name: className });
    window.open(url, '_blank', 'noopener,noreferrer');
    return url;
}

export async function openStudentPdf(data, studentId) {
    const url = await getBlobUrl('/reports/student-pdf', { data, student_id: studentId });
    window.open(url, '_blank', 'noopener,noreferrer');
    return url;
}

// ── Health / Config ───────────────────────────────────────────────
export async function getHealth() {
    return json('/health');
}

export async function getConfig() {
    return json('/config');
}
