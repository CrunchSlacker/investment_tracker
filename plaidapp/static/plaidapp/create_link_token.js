function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

fetch("/plaid/create_link_token/")
  .then((res) => res.json())
  .then((data) => {
    const handler = Plaid.create({
      token: data.link_token,
      onSuccess: function (public_token, metadata) {
        console.log("Plaid Link Success, got public_token:", public_token);
        const institution_id = metadata.institution?.institution_id || null;

        fetch("/plaid/exchange_public_token/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify({
            public_token: public_token,
            institution_id: institution_id,
          }),
        })
          .then((res) => res.json())
          .then((data) => {
            console.log("Exchange response:", data);
            window.location.reload(true);
          })
          .catch((err) => {
            console.error("Exchange error:", err);
          });
      },

      onExit: function (err, metadata) {
        console.warn("User exited Plaid Link:", err, metadata);
      },
    });

    const button = document.getElementById("link-button");
    if (button) {
      button.addEventListener("click", () => {
        handler.open();
      });
    } else {
      console.error("No #link-button found on page.");
    }
  })
  .catch((err) => {
    console.error("Failed to create link token:", err);
  });
