const target = `${import.meta.env.BASE_URL}${window.location.search}${window.location.hash}`;

window.location.replace(target);
