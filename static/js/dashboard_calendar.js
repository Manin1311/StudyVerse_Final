
/* ========================================
   CALENDAR & EVENT LOGIC
   ======================================== */
document.addEventListener('DOMContentLoaded', () => {

    // --- 1. Global State ---
    const today = new Date();
    let currentMonth = today.getMonth(); // 0-11
    let currentYear = today.getFullYear();
    let selectedDate = formatDate(today); // "YYYY-MM-DD"

    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

    // Elements
    const monthLabel = document.querySelector('.cal-header span');
    const dayGrid = document.querySelector('.cal-days-grid');
    const prevBtn = document.querySelector('.cal-nav-btn:first-child');
    const nextBtn = document.querySelector('.cal-nav-btn:last-child');
    const timelineInfo = document.querySelector('.timeline-info');
    const eventPlaceholder = document.querySelector('.event-placeholder');
    const initEventBtn = document.querySelector('.btn-init-event');

    // --- 2. Helper Functions ---
    function formatDate(date) {
        // Returns YYYY-MM-DD local
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    }

    function renderCalendar(month, year) {
        // Update header
        monthLabel.textContent = `${monthNames[month]} ${year}`;

        // Clear old days (keep labels)
        const labels = Array.from(dayGrid.children).slice(0, 7);
        dayGrid.innerHTML = '';
        labels.forEach(l => dayGrid.appendChild(l));

        const firstDay = new Date(year, month, 1).getDay(); // 0 (Sun) - 6 (Sat)
        const daysInMonth = new Date(year, month + 1, 0).getDate();

        // Empty slots for previous month
        for (let i = 0; i < firstDay; i++) {
            const empty = document.createElement('div');
            empty.className = 'cal-day empty';
            dayGrid.appendChild(empty);
        }

        // Days
        for (let d = 1; d <= daysInMonth; d++) {
            const cell = document.createElement('div');
            cell.className = 'cal-day';
            cell.textContent = d;

            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            cell.dataset.date = dateStr;

            if (dateStr === selectedDate) {
                cell.classList.add('active');
            }

            // Interaction
            cell.addEventListener('click', () => {
                document.querySelectorAll('.cal-day.active').forEach(el => el.classList.remove('active'));
                cell.classList.add('active');
                selectedDate = dateStr;
                updateTimelineForDate(dateStr);
            });

            dayGrid.appendChild(cell);
        }
    }

    function updateTimelineForDate(dateStr) {
        // Update header info "Timeline // Jan 25"
        const d = new Date(dateStr);
        // Fix timezone offset issue for pure display logic or just parse manually
        const parts = dateStr.split('-');
        const displayDate = new Date(parts[0], parts[1] - 1, parts[2]);

        const dayName = displayDate.toLocaleString('default', { month: 'short', day: 'numeric' });
        timelineInfo.innerHTML = `<i class="fa-regular fa-clock"></i> Timeline // ${dayName}`;

        // Fetch events from API
        eventPlaceholder.innerHTML = `<div style="padding: 20px; text-align: center;"><i class="fa-solid fa-spinner fa-spin"></i></div>`;

        fetch(`/api/events?date=${dateStr}`)
            .then(r => r.json())
            .then(data => {
                const events = data.events;
                if (events.length === 0) {
                    eventPlaceholder.innerHTML = `
                        <i class="fa-regular fa-clock"></i>
                        <div style="font-size: 0.85rem; font-weight: 600;">Zero Collisions Detected</div>
                        <div style="font-size: 0.7rem;">No scheduled events for today</div>
                    `;
                } else {
                    let html = `<div style="display: flex; flex-direction: column; gap: 10px; width: 100%;">`;
                    events.forEach(e => {
                        html += `
                            <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 12px; border-left: 3px solid var(--accent-green); text-align: left;">
                                <div style="display: flex; justify-content: space-between;">
                                    <div style="font-weight: 700; color: #fff;">${e.title}</div>
                                    <div style="font-size: 0.75rem; color: var(--accent-green);">${e.time || ''}</div>
                                </div>
                                <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px;">${e.description}</div>
                            </div>
                        `;
                    });
                    html += `</div>`;
                    eventPlaceholder.innerHTML = html;
                    // remove placeholder styling if full
                    eventPlaceholder.style.border = 'none';
                }
            });
    }

    // --- 3. Event Creation Modal ---
    function openCreateEventModal() {
        const title = prompt("Event Title:");
        if (!title) return;

        const desc = prompt("Description (optional):");
        const time = prompt("Time (HH:MM) optional:", "12:00");

        fetch('/api/events', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: title,
                description: desc,
                date: selectedDate,
                time: time
            })
        })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    updateTimelineForDate(selectedDate);
                } else {
                    alert("Failed to create event");
                }
            });
    }

    // --- 4. Event Reminder Popup Check ---
    function checkReminders() {
        fetch('/api/events/check-warnings')
            .then(r => r.json())
            .then(data => {
                if (data.has_warning && data.event) {
                    showEventPopup(data.event);
                }
            });
    }

    function showEventPopup(event) {
        // Create custom modal matching system UI
        const modalId = 'event-popup-' + event.id;
        if (document.getElementById(modalId)) return; // already showing

        const modal = document.createElement('div');
        modal.id = modalId;
        modal.className = 'modal-overlay';
        modal.style.display = 'flex';
        modal.style.background = 'rgba(0,0,0,0.85)';
        modal.style.zIndex = '3000';

        modal.innerHTML = `
            <div class="modal-content" style="background: #111; border: 1px solid var(--accent-green); padding: 30px; border-radius: 20px; width: 400px; text-align: center; position: relative; box-shadow: 0 0 50px rgba(74, 222, 128, 0.2);">
                <div style="background: rgba(74, 222, 128, 0.1); width: 60px; height: 60px; border-radius: 50%; border: 2px solid var(--accent-green); display: grid; place-items: center; margin: 0 auto 20px;">
                    <i class="fa-regular fa-bell" style="font-size: 1.5rem; color: var(--accent-green);"></i>
                </div>
                <h2 style="color: #fff; font-family: var(--font-heading); margin-bottom: 10px;">Event Reminder</h2>
                <div style="font-size: 1.2rem; font-weight: 700; color: #fff; margin-bottom: 5px;">${event.title}</div>
                <div style="color: var(--text-secondary); margin-bottom: 24px;">${event.description || 'Happening today!'} at ${event.time || 'All Day'}</div>
                
                <button id="btn-dismiss-${event.id}" class="btn-primary" style="width: 100%; padding: 12px; border-radius: 10px; background: var(--accent-green); color: #000; font-weight: 700; border: none; cursor: pointer;">
                    Acknowledge
                </button>
            </div>
        `;

        document.body.appendChild(modal);

        // Dismiss Logic
        document.getElementById(`btn-dismiss-${event.id}`).addEventListener('click', () => {
            fetch(`/api/events/${event.id}/dismiss`, { method: 'POST' })
                .then(() => {
                    modal.remove();
                });
        });
    }

    // --- 5. Initializers ---
    renderCalendar(currentMonth, currentYear);
    updateTimelineForDate(selectedDate); // Load today's events initially
    checkReminders(); // Check for warnings on load

    // Poll for reminders every 30 seconds
    setInterval(checkReminders, 30000);

    // Listeners
    prevBtn.addEventListener('click', () => {
        currentMonth--;
        if (currentMonth < 0) { currentMonth = 11; currentYear--; }
        renderCalendar(currentMonth, currentYear);
    });

    nextBtn.addEventListener('click', () => {
        currentMonth++;
        if (currentMonth > 11) { currentMonth = 0; currentYear++; }
        renderCalendar(currentMonth, currentYear);
    });

    initEventBtn.addEventListener('click', openCreateEventModal);
});
