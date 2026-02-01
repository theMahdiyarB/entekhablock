// static/js/vote.js
// Simplified Voting Management for Entekhablock MVP

class VoteManager {
    constructor() {
        this.selectedOption = null;
        this.pollId = window.POLL_ID;
    }

    init() {
        console.log("[VoteManager] Initializing for poll:", this.pollId);
        this.setupVoteOptions();
        this.setupForm();
    }

    setupVoteOptions() {
        const optionCards = document.querySelectorAll('.option-card');
        const submitBtn = document.getElementById('submit-btn');
        const previewBtn = document.getElementById('preview-btn');

        optionCards.forEach(card => {
            const input = card.querySelector('input[type="radio"]');

            card.addEventListener('click', () => {
                input.checked = true;
                this.updateSelection(card);
            });

            input.addEventListener('change', () => {
                this.updateSelection(card);
            });
        });
    }

    updateSelection(selectedCard) {
        // Remove active class from all
        document.querySelectorAll('.option-card').forEach(c => c.classList.remove('active'));

        // Add to selected
        selectedCard.classList.add('active');
        this.selectedOption = selectedCard.querySelector('input').value;

        // Enable buttons
        const submitBtn = document.getElementById('submit-btn');
        const previewBtn = document.getElementById('preview-btn');
        if (submitBtn) submitBtn.disabled = false;
        if (previewBtn) previewBtn.disabled = false;

        console.log("[VoteManager] Selected:", this.selectedOption);
    }

    setupForm() {
        const form = document.getElementById('vote-form');
        const previewBtn = document.getElementById('preview-btn');
        const modal = document.getElementById('preview-modal');
        const closeModal = document.getElementById('close-modal');
        const confirmBtn = document.getElementById('confirm-btn');
        const editBtn = document.getElementById('edit-btn');

        if (previewBtn && modal) {
            previewBtn.addEventListener('click', () => {
                document.getElementById('selected-option').textContent = this.selectedOption;
                modal.classList.add('show');
            });
        }

        if (closeModal) closeModal.addEventListener('click', () => modal.classList.remove('show'));
        if (editBtn) editBtn.addEventListener('click', () => modal.classList.remove('show'));

        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => {
                form.submit();
            });
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new VoteManager().init();
});
