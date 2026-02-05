/**
 * Configures a Persian Datepicker with Material Design 3 styling and behavior.
 *
 * @param {string} inputId - The ID of the visible input field (e.g., '#birth_date_input')
 * @param {string} hiddenInputId - The ID of the hidden input field to store the YYYY-MM-DD value (e.g., '#birth_date')
 * @param {boolean} initialValue - Whether to set the initial value (default: false)
 */
function setupPersianDatepicker(inputId, hiddenInputId, initialValue = false) {
    console.log(`Setting up datepicker for ${inputId}`);
    const $input = $(inputId);
    const $hiddenInput = $(hiddenInputId);

    if ($input.length === 0) {
        console.error(`Input ${inputId} not found!`);
        return;
    }

    if (typeof $input.pDatepicker !== 'function') {
        console.error("pDatepicker function not found on jQuery object. Is the library loaded?");
        return;
    }

    // Helper to convert Persian/Arabic digits to English
    function toEnglishDigits(str) {
        if (!str) return str;
        return str.replace(/[\u0660-\u0669\u06f0-\u06f9]/g, function (c) {
            return c.charCodeAt(0) & 0xf;
        });
    }

    // Initialize the datepicker
    $input.pDatepicker({
        format: 'YYYY/MM/DD',
        autoClose: true,
        initialValue: initialValue,
        calendar: {
            persian: {
                locale: 'fa'
            }
        },
        toolbox: {
            calendarSwitch: {
                enabled: false
            }
        },
        onSelect: function(unix) {
            console.log("Date selected via picker");
            setTimeout(() => {
                let val = $input.val();
                if (val) {
                    // Convert to English digits just in case the picker put Persian ones
                    val = toEnglishDigits(val);

                    // Update visible input to match (optional, but good for consistency)
                    if ($input.val() !== val) {
                        $input.val(val);
                    }

                    const formatted = val.replace(/\//g, '-');
                    $hiddenInput.val(formatted);

                    $hiddenInput.trigger('change');
                    $input.parent().addClass('has-value');
                }
            }, 0);
        }
    });

    // Improved Input Masking Logic for YYYY/MM/DD
    $input.on('input', function(e) {
        let input = this.value;

        // Convert to English digits immediately
        input = toEnglishDigits(input);

        // Remove any non-digit characters
        let raw = input.replace(/\D/g, '');

        // Limit to 8 digits (YYYYMMDD)
        if (raw.length > 8) {
            raw = raw.substring(0, 8);
        }

        let formatted = '';

        if (raw.length > 0) {
            // Add Year
            formatted += raw.substring(0, 4);
        }

        if (raw.length >= 5) {
            // Add Month slash
            formatted += '/' + raw.substring(4, 6);
        }

        if (raw.length >= 7) {
            // Add Day slash
            formatted += '/' + raw.substring(6, 8);
        }

        // Update input if different
        if (this.value !== formatted) {
             this.value = formatted;
        }

        // Update hidden input if full date is entered
        if (formatted.length === 10) {
             const hiddenVal = formatted.replace(/\//g, '-');
             $hiddenInput.val(hiddenVal);
             console.log("Hidden input updated:", hiddenVal);
        }
    });

    // Check initial state
    if ($input.val()) {
        $input.parent().addClass('has-value');
    }
}

/**
 * Global utility to convert Persian/Arabic digits to English digits
 * Can be used by other scripts
 */
window.toEnglishDigits = function(str) {
    if (!str) return str;
    return str.replace(/[\u0660-\u0669\u06f0-\u06f9]/g, function (c) {
        return c.charCodeAt(0) & 0xf;
    });
};
