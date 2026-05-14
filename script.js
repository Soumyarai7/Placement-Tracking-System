document.addEventListener('DOMContentLoaded', () => {
    // Toggle Status functionality for Admin Dashboard
    const toggleButtons = document.querySelectorAll('.toggle-btn');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            const studentId = e.target.getAttribute('data-id');
            const badge = document.getElementById(`status-badge-${studentId}`);
            const originalText = button.textContent;
            
            button.textContent = '...';
            button.disabled = true;
            
            try {
                const response = await fetch(`/admin/toggle_shortlist/${studentId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                const result = await response.json();
                
                if (result.success) {
                    if (result.is_shortlisted) {
                        badge.textContent = 'Shortlisted';
                        badge.className = 'status-badge success';
                    } else {
                        badge.textContent = 'Pending';
                        badge.className = 'status-badge pending';
                    }
                } else {
                    alert('Failed to update status.');
                }
            } catch (error) {
                console.error('Error toggling status:', error);
                alert('An error occurred.');
            } finally {
                button.textContent = originalText;
                button.disabled = false;
            }
        });
    });

    // Auto-dismiss flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    if (flashMessages.length > 0) {
        setTimeout(() => {
            flashMessages.forEach(msg => {
                msg.style.opacity = '0';
                setTimeout(() => msg.remove(), 500); // Wait for transition
            });
        }, 5000);
    }
});
