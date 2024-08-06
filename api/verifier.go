package handler

import (
	"encoding/json"
	"fmt"
	"net/http"

	emailVerifier "github.com/AfterShip/email-verifier"
	"github.com/julienschmidt/httprouter"
)

func Handler(w http.ResponseWriter, r *http.Request, ps httprouter.Params) {
	verifier := emailVerifier.NewVerifier()
	ret, err := verifier.Verify(ps.ByName("email"))
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	if !ret.Syntax.Valid {
		_, _ = fmt.Fprint(w, "email address syntax is invalid")
		return
	}

	bytes, err := json.Marshal(ret)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}

	// _, _ = fmt.Fprint(w, string(bytes))
	fmt.Fprintf(w, string(bytes))

}
