function checkUser() {
    const isLoggedIn = localStorage.getItem("isLoggedIn");
    const userId = localStorage.getItem("userId");

    if (!isLoggedIn || !userId) {
        window.location.href = 'signin-new.html';
        return false;
    }
    return true;
}

function logout() {
    if (confirm('Are you sure you want to log out?')) {
        localStorage.removeItem('userId');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('isLoggedIn');
        window.location.href = 'signin-new.html';
    }
}

function logoutOption() {
    const isLoggedIn = localStorage.getItem('isLoggedIn');

    if (isLoggedIn) {
        const navTabs = document.getElementById('navTabs');

        if (navTabs && !document.getElementById('logoutBtn')) {
            const logoutBtn = document.createElement('button');
            logoutBtn.id = 'logoutBtn';
            logoutBtn.className = 'tab logout-btn';
            logoutBtn.textContent = 'Logout';
            logoutBtn.onclick = logout;
            navTabs.appendChild(logoutBtn);
        }
    }
}

function getCurrentUserId() {
    return localStorage.getItem('userId');
}

checkUser();
logoutOption();

  // Login user
async function loginUser(email, password) {
    try {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading-spinner"></span>Signing in...';
            
        const res = await fetch('https://project-iqv0.onrender.com/loginEmail', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
            
        const data = await res.json();
            
        if (!res.ok) {
            showToast('Login Failed', data.error || 'Invalid email or password. Please try again.');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Sign In';
            return;
        }
            
        localStorage.setItem('userId', data.userId);
        localStorage.setItem('userEmail', email);
        localStorage.setItem('isLoggedIn', 'true');
            
        showToast('Welcome Back!', 'Login successful! Redirecting...', 'success');
            
        // Redirect to the signin page after a short delay
        setTimeout(() => {
            window.location.href = 'signin-new.html';
        }, 1500);
            
    } catch (error) {
        showToast('Network Error', 'Unable to connect to server. Please check your connection.');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Sign In';
    }
}

