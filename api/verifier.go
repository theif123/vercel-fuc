package Handler

import (
	"encoding/json"
	"net/http"

	"github.com/badoux/checkmail"
	"github.com/julienschmidt/httprouter"
)

// Vercel expects the exported function to be named Handler and match the signature func(http.ResponseWriter, *http.Request)
func Handler(w http.ResponseWriter, r *http.Request) {
	// Initialize the email verifier
	// verifier := emailVerifier.NewVerifier()

	// Extract the email from the request path
	params := httprouter.ParamsFromContext(r.Context())
	email := params.ByName("email")

	// Verify the email address
	ret, err := checkmail.ValidateForma(email)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Check if the email syntax is valid
	// if !ret.Syntax.Valid {
	// 	fmt.Fprint(w, "email address syntax is invalid")
	// 	return
	// }

	// Marshal the verification result to JSON
	bytes, err := json.Marshal(ret)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Send the JSON response
	w.Header().Set("Content-Type", "application/json")
	w.Write(bytes)
}
