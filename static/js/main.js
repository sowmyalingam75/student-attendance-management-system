/**
 * Student Attendance Management System - Main Client-Side JavaScript
 * Pure Vanilla JavaScript implementation
 */

document.addEventListener('DOMContentLoaded', () => {
    initSidebarToggle();
    initPasswordToggle();
    initTableSearch();
    initAttendanceMarkingControls();
    initDeleteModal();
    initToastAutoDismiss();
    initQuickCredFill();
    initPrintButtons();
});

/* -------------------------------------------------------------------------
   1. Sidebar Toggle (Mobile / Responsive)
   ------------------------------------------------------------------------- */
function initSidebarToggle() {
    const toggleBtn = document.getElementById('sidebarToggleBtn');
    const sidebar = document.querySelector('.app-sidebar');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            sidebar.classList.toggle('show');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 992 && sidebar.classList.contains('show') && !sidebar.contains(e.target)) {
                sidebar.classList.remove('show');
            }
        });
    }
}

/* -------------------------------------------------------------------------
   2. Password Visibility Toggle
   ------------------------------------------------------------------------- */
function initPasswordToggle() {
    const toggleButtons = document.querySelectorAll('.password-toggle-btn');
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target') || 'password';
            const input = document.getElementById(targetId);
            const icon = btn.querySelector('i');

            if (input) {
                if (input.type === 'password') {
                    input.type = 'text';
                    if (icon) {
                        icon.classList.remove('fa-eye');
                        icon.classList.add('fa-eye-slash');
                    }
                } else {
                    input.type = 'password';
                    if (icon) {
                        icon.classList.remove('fa-eye-slash');
                        icon.classList.add('fa-eye');
                    }
                }
            }
        });
    });
}

/* -------------------------------------------------------------------------
   3. Instant Table Search & Filter
   ------------------------------------------------------------------------- */
function initTableSearch() {
    const searchInputs = document.querySelectorAll('.table-search-input');
    searchInputs.forEach(input => {
        input.addEventListener('keyup', (e) => {
            const filterValue = e.target.value.toLowerCase().trim();
            const tableId = input.getAttribute('data-table') || 'searchableTable';
            const table = document.getElementById(tableId);

            if (table) {
                const tbody = table.querySelector('tbody') || table;
                const rows = tbody.querySelectorAll('tr');

                rows.forEach(row => {
                    const text = row.innerText.toLowerCase();
                    if (text.includes(filterValue)) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });
            }
        });
    });
}

/* -------------------------------------------------------------------------
   4. Attendance Marking Controls (Mark All Present / Absent & Live Counter)
   ------------------------------------------------------------------------- */
function initAttendanceMarkingControls() {
    const markAllPresentBtn = document.getElementById('markAllPresentBtn');
    const markAllAbsentBtn = document.getElementById('markAllAbsentBtn');
    const attendanceForm = document.getElementById('attendanceForm');

    if (markAllPresentBtn) {
        markAllPresentBtn.addEventListener('click', () => {
            const presentRadios = document.querySelectorAll('input[type="radio"][value="Present"]');
            presentRadios.forEach(radio => {
                radio.checked = true;
            });
            updateAttendanceSummary();
        });
    }

    if (markAllAbsentBtn) {
        markAllAbsentBtn.addEventListener('click', () => {
            const absentRadios = document.querySelectorAll('input[type="radio"][value="Absent"]');
            absentRadios.forEach(radio => {
                radio.checked = true;
            });
            updateAttendanceSummary();
        });
    }

    // Live update on individual change
    if (attendanceForm) {
        const radios = attendanceForm.querySelectorAll('input[type="radio"]');
        radios.forEach(radio => {
            radio.addEventListener('change', updateAttendanceSummary);
        });
        updateAttendanceSummary();
    }
}

function updateAttendanceSummary() {
    const presentCountEl = document.getElementById('summaryPresentCount');
    const absentCountEl = document.getElementById('summaryAbsentCount');
    const totalCountEl = document.getElementById('summaryTotalCount');

    const presentChecked = document.querySelectorAll('input[type="radio"][value="Present"]:checked').length;
    const absentChecked = document.querySelectorAll('input[type="radio"][value="Absent"]:checked').length;
    const total = presentChecked + absentChecked;

    if (presentCountEl) presentCountEl.innerText = presentChecked;
    if (absentCountEl) absentCountEl.innerText = absentChecked;
    if (totalCountEl) totalCountEl.innerText = total;
}

/* -------------------------------------------------------------------------
   5. Delete Confirmation Modal
   ------------------------------------------------------------------------- */
function initDeleteModal() {
    const modal = document.getElementById('deleteConfirmModal');
    const confirmForm = document.getElementById('deleteConfirmForm');
    const itemNameEl = document.getElementById('deleteItemName');
    const cancelBtn = document.getElementById('deleteModalCancelBtn');
    const closeBtn = document.getElementById('deleteModalCloseBtn');

    if (!modal) return;

    // Trigger buttons
    document.querySelectorAll('.btn-trigger-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const actionUrl = btn.getAttribute('data-action');
            const itemName = btn.getAttribute('data-name') || 'this item';

            if (confirmForm && actionUrl) {
                confirmForm.action = actionUrl;
            }
            if (itemNameEl) {
                itemNameEl.innerText = itemName;
            }
            modal.classList.add('active');
        });
    });

    const closeModal = () => modal.classList.remove('active');

    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
}

/* -------------------------------------------------------------------------
   6. Toast Message Auto-Dismiss
   ------------------------------------------------------------------------- */
function initToastAutoDismiss() {
    const toasts = document.querySelectorAll('.toast-message');
    toasts.forEach(toast => {
        // Auto close after 4.5 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(20px)';
            setTimeout(() => toast.remove(), 300);
        }, 4500);

        const closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => toast.remove());
        }
    });
}

/* -------------------------------------------------------------------------
   7. Quick Credential Fill for Instant Demo Login
   ------------------------------------------------------------------------- */
function initQuickCredFill() {
    const buttons = document.querySelectorAll('.btn-cred-fill');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            const username = btn.getAttribute('data-user');
            const password = btn.getAttribute('data-pass');
            const userField = document.getElementById('username');
            const passField = document.getElementById('password');

            if (userField && passField) {
                userField.value = username;
                passField.value = password;
                userField.focus();
            }
        });
    });
}

/* -------------------------------------------------------------------------
   8. Print Button Handler
   ------------------------------------------------------------------------- */
function initPrintButtons() {
    const printBtns = document.querySelectorAll('.btn-print-page');
    printBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            window.print();
        });
    });
}
