fetch("/plaid/create_link_token/")
  .then((res) => res.json())
  .then((data) => {
    const handler = Plaid.create({
      token: data.link_token,
      onSuccess: function (public_token, metadata) {
        fetch("/plaid/exchange_public_token/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": "{{ csrf_token }}",
          },
          body: JSON.stringify({ public_token: public_token }),
        })
          .then((res) => res.json())
          .then(console.log);
      },
      onExit: function (err, metadata) {
        console.log(err, metadata);
      },
    });

    document.getElementById("link-button").onclick = function () {
      handler.open();
    };
  });
