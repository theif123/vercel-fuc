package handler

import (
	"encoding/json"
	"net"
	"net/http"
	"net/mail"
	"strings"
)

type EmailValidationResponse struct {
	Email       string `json:"email"`
	FormatValid bool   `json:"format_valid"`
	MXValid     bool   `json:"mx_valid"`
	Error       string `json:"error,omitempty"`
}

func validateEmail(email string) EmailValidationResponse {
	response := EmailValidationResponse{Email: email}

	// 验证邮箱格式
	_, err := mail.ParseAddress(email)
	if err != nil {
		response.FormatValid = false
		response.Error = "Invalid email format"
		return response
	}
	response.FormatValid = true

	// 获取域名
	domain := strings.Split(email, "@")[1]

	// 验证MX记录
	mxRecords, err := net.LookupMX(domain)
	if err != nil || len(mxRecords) == 0 {
		response.MXValid = false
		response.Error = "Domain does not have MX records"
		return response
	}
	response.MXValid = true

	return response
}

func handler(w http.ResponseWriter, r *http.Request) {
	email := r.URL.Query().Get("email")
	if email == "" {
		http.Error(w, "Email is required", http.StatusBadRequest)
		return
	}

	validationResponse := validateEmail(email)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(validationResponse)
}
