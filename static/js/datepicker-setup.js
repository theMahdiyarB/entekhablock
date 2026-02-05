/**
 * Configures a Persian Datepicker with Material Design 3 styling and behavior.
 *
 * @param {string} inputId - The ID of the visible input field (e.g., '#birth_date_input')
 * @param {string} hiddenInputId - The ID of the hidden input field to store the YYYY-MM-DD value (e.g., '#birth_date')
 * @param {boolean} initialValue - Whether to set the initial value (default: false)
 */
function setupPersianDatepicker(inputId, hiddenInputId, initialValue = false) {
    const $input = $(inputId);
    const $hiddenInput = $(hiddenInputId);

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
            // The library sets the visible input value based on format 'YYYY/MM/DD'
            // We need to update the hidden input with 'YYYY-MM-DD'
            // Wait a tick for the input to update
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

    // Input Masking Logic for YYYY/MM/DD
    $input.on('input', function(e) {
        let val = this.value.replace(/\D/g, ''); // Remove non-digits

        // Prevent typing more than 8 digits
        if (val.length > 8) {
            val = val.substring(0, 8);
        }

        // Add slashes
        if (val.length >= 5) {
            val = val.substring(0, 4) + '/' + val.substring(4);
        }
        if (val.length >= 8) {
            val = val.substring(0, 7) + '/' + val.substring(7);
        }

        this.value = val;

        // Update hidden input if full date is entered
        if (val.length === 10) {
             const formatted = val.replace(/\//g, '-');
             $hiddenInput.val(formatted);
        } else {
            // Optional: clear hidden input if invalid?
            // Better to keep it or handle valid logic elsewhere
        }
    });

    // Fix for floating label when value is present
    $input.on('blur', function() {
        if (this.value) {
             $input.addClass('has-value'); // Ensure label stays up
        }
    });

    // Check initial state
    if ($input.val()) {
        $input.addClass('has-value');
    }
}
