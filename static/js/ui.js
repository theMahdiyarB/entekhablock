// Material Design 3 Interaction Scripts

document.addEventListener('DOMContentLoaded', () => {

    /* =========================================
       Character Counter Logic
       ========================================= */
    const inputsWithCounters = document.querySelectorAll('input[maxlength], textarea[maxlength]');

    inputsWithCounters.forEach(input => {
        // Find the closest wrapper to locate the counter
        const wrapper = input.closest('.text-field-wrapper');
        if (!wrapper) return;

        const counterElement = wrapper.querySelector('.character-counter');
        if (!counterElement) return;

        const maxLength = input.getAttribute('maxlength');

        const updateCounter = () => {
            const currentLength = input.value.length;
            counterElement.textContent = `${currentLength}/${maxLength}`;
        };

        // Initial update
        updateCounter();

        // Update on input
        input.addEventListener('input', updateCounter);
    });

    /* =========================================
       Ripple Effect (Optional enhancement)
       ========================================= */
    // Add simple ripple if needed in future
});
