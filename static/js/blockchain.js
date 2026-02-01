document.addEventListener('DOMContentLoaded', () => {
    // Initial state: Collapse all blocks except Genesis
    document.querySelectorAll('.block-item').forEach(block => {
        const blockIndex = parseInt(block.dataset.blockIndex, 10);
        if (blockIndex !== 0) {
            block.classList.add('collapsed');
        } else {
            block.classList.add('expanded'); // Genesis block is expanded by default
        }
    });
    // Truncate long hash values for better readability
    truncateAllHashes();
});

// Toggle a single block's visibility
function toggleBlock(blockIndex) {
    const block = document.querySelector(`.block-item[data-block-index='${blockIndex}']`);
    const blockDetails = document.getElementById(`block-${blockIndex}`);

    if (block && blockDetails) {
        // Toggle 'expanded' and 'collapsed' classes on the parent
        block.classList.toggle('expanded');
        block.classList.toggle('collapsed');

        // Toggle visibility of the details section
        if (block.classList.contains('expanded')) {
            blockDetails.style.display = 'block';
        } else {
            blockDetails.style.display = 'none';
        }
    }
}


// Toggle all blocks' visibility at once
function toggleAllBlocks() {
    const blocks = document.querySelectorAll('.block-item');
    // Check if any block is currently collapsed
    const isAnyCollapsed = Array.from(blocks).some(b => b.classList.contains('collapsed'));

    blocks.forEach(block => {
        const blockIndex = block.dataset.blockIndex;
        const blockDetails = document.getElementById(`block-${blockIndex}`);

        if (isAnyCollapsed) {
            // If any are collapsed, expand all
            block.classList.remove('collapsed');
            block.classList.add('expanded');
            blockDetails.style.display = 'block';
        } else {
            // If all are expanded, collapse all
            block.classList.add('collapsed');
            block.classList.remove('expanded');
            blockDetails.style.display = 'none';
        }
    });
}

// Search for a block by index, hash, or date
document.getElementById('searchBlock').addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase();

    document.querySelectorAll('.block-item').forEach(block => {
        const blockIndex = block.dataset.blockIndex;
        const blockTimestamp = block.querySelector('.block-time').textContent.toLowerCase();
        const blockHash = block.querySelector('.hash-value[title]')?.title.toLowerCase() || '';

        if (
            blockIndex.includes(searchTerm) ||
            blockTimestamp.includes(searchTerm) ||
            blockHash.includes(searchTerm)
        ) {
            block.style.display = 'flex';
        } else {
            block.style.display = 'none';
        }
    });
});


// Verify the entire blockchain's integrity
async function verifyChain() {
    try {
        const response = await fetch('/api/blockchain/is_valid');
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();

        if (data.is_valid) {
            showNotification('✅ بلاک‌چین معتبر است.', 'success');
        } else {
            showNotification('⚠️ هشدار: بلاک‌چین نامعتبر است!', 'error');
        }
        // Reload to show updated validity status on blocks
        setTimeout(() => location.reload(), 2000);
    } catch (error) {
        console.error("Verification failed:", error);
        showNotification('❌ خطا در تأیید اعتبار بلاک‌چین.', 'error');
    }
}

// Simulate tampering with a block for demonstration
async function simulateTampering() {
    const blockIndexToTamper = prompt("برای شبیه‌سازی دستکاری، شماره بلاک مورد نظر را وارد کنید (مثلا 1):", "1");
    if (!blockIndexToTamper || isNaN(blockIndexToTamper)) return;

    try {
        const response = await fetch(`/api/blockchain/tamper/${blockIndexToTamper}`, { method: 'POST' });
        const data = await response.json();

        if (!response.ok) {
            showNotification(data.message || 'خطا در دستکاری', 'error');
            return;
        }

        showNotification(data.message, 'warning');
        // Reload to reflect the tampered state
        setTimeout(() => location.reload(), 2000);

    } catch (error) {
        console.error("Tampering simulation failed:", error);
        showNotification('❌ خطا در ارتباط با سرور.', 'error');
    }
}


// Copy text to clipboard and show a notification
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('✓ کپی شد!');
    }, (err) => {
        console.error('Could not copy text: ', err);
        showNotification('❌ خطا در کپی کردن.', 'error');
    });
}

// Show a notification message
function showNotification(message, type = 'success') {
    const notification = document.getElementById('copyNotification');
    if (!notification) return;

    notification.textContent = message;
    notification.className = 'copy-notification show';

    // Change color based on type
    if (type === 'error') {
        notification.style.backgroundColor = 'var(--m3-error)';
        notification.style.color = 'var(--m3-on-error)';
    } else if (type === 'warning') {
        notification.style.backgroundColor = '#FFA500'; // Orange for warning
        notification.style.color = '#000';
    } else {
        notification.style.backgroundColor = 'var(--m3-success)';
        notification.style.color = 'var(--m3-on-success)';
    }

    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Truncate long hash strings for cleaner UI
function truncateAllHashes() {
    document.querySelectorAll('.hash-value').forEach(el => {
        const fullHash = el.getAttribute('title') || el.textContent;
        if (fullHash.length > 32) {
            el.textContent = `${fullHash.substring(0, 16)}...${fullHash.substring(fullHash.length - 16)}`;
        }
    });
}