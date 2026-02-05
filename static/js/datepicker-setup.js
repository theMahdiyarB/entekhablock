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
            // The library sets the visible input value based on format 'YYYY/MM/DD'
            // We need to update the hidden input with 'YYYY-MM-DD'
            setTimeout(() => {
                const val = $input.val();
                if (val) {
                    const formatted = val.replace(/\//g, '-');
                    $hiddenInput.val(formatted);

                    // Trigger change event if needed for other listeners
                    $hiddenInput.trigger('change');

                    // Update floating label state
                    $input.parent().addClass('has-value');
                }
            }, 0);
        }
    });

    // Improved Input Masking Logic for YYYY/MM/DD
    $input.on('input', function(e) {
        let input = this.value;

        // Remove any non-digit characters to process raw numbers
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

        // Only update if the value is different to avoid cursor jumping issues (mostly)
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

    // Fix for floating label when value is present
    $input.on('blur', function() {
        if (this.value) {
             // In M3 CSS logic, :not(:placeholder-shown) handles this, but sometimes helper classes are needed
             // With the current CSS, placeholder=" " and valid value should work.
        }
    });

    // Check initial state
    if ($input.val()) {
        $input.parent().addClass('has-value'); // Ensure label stays up
    }
}
