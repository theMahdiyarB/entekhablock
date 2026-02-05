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
       Global Persian Digit Converter
       ========================================= */
    const numericInputs = document.querySelectorAll('input[type="number"], input[pattern*="0-9"], input.numeric-only');

    // Helper function (duplicate of what is in datepicker-setup.js to ensure independence)
    function toEnglishDigits(str) {
        if (!str) return str;
        return str.replace(/[\u0660-\u0669\u06f0-\u06f9]/g, function (c) {
            return c.charCodeAt(0) & 0xf;
        });
    }

    numericInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            const original = this.value;
            const converted = toEnglishDigits(original);
            if (original !== converted) {
                // Determine cursor position to maintain it
                const start = this.selectionStart;
                const end = this.selectionEnd;

                this.value = converted;

                // Restore cursor if supported
                if (this.setSelectionRange) {
                    this.setSelectionRange(start, end);
                }
            }
        });
    });
});
