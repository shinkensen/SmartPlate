
function checkUser(){
    const isLoggedIn = localStorage.getItem("isLoggedIn");
    const userId = localStorage.getItem('userId');

    if (!isLoggedIn || !userId){
        window.location.href('signup-new.html');
        return false;
    }
    return true;
}

function logout(){
    if (confirm('Are you sure you want to log out?')){
        localStorage.removeItem('userId');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('isLoggedIn');
        window.location.href('signin-new.html');
    }
}

function logoutOption(){
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    if (isLoggedIn) {
        const navTabs = document.getElementbyId('logoutBtn');
        if (navTabs) {
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
