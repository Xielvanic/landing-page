document.addEventListener('DOMContentLoaded', function() {
    const toggleButton = document.getElementById('toggle-dark-mode');
    toggleButton.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
    });
});

function toggleEditForm(itemId) {
    const form = document.getElementById(`edit-form-${itemId}`);
    if (form) {
        form.style.display = form.style.display === 'none' ? 'block' : 'none';
    } else {
        console.error(`Edit form with ID edit-form-${itemId} not found.`);
    }
}

function connectSSH(ip) {
    window.open(`ssh://${ip}`, '_blank');
}

function connectRDP(ip) {
    window.open(`rdp://${ip}`, '_blank');
}

function confirmDelete(itemId) {
    if (confirm('Are you sure you want to delete this item?')) {
        fetch(`/delete_item/${itemId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (response.ok) {
                    location.reload(); // Reload the page to reflect changes
                } else {
                    console.error('Failed to delete item.');
                }
            })
            .catch(error => console.error('Error deleting item:', error));
    }
}