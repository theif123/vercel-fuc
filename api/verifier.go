package handler

import (
	"encoding/json"
	"net"
	"net/http"
	"net/mail"
	"strings"
)

// EmailValidationResponse 定义返回的单个邮箱验证结果
type EmailValidationResponse struct {
	Email       string `json:"email"`
	FormatValid bool   `json:"format_valid"`
	MXValid     bool   `json:"mx_valid"`
	Error       string `json:"error,omitempty"`
}

// EmailsRequest 定义请求体结构
type EmailsRequest struct {
	Emails []string `json:"emails"`
}

// validateEmail 进行格式验证和 MX 记录验证
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

	// 提取域名
	domain := strings.Split(email, "@")[1]

	// 验证 MX 记录
	mxRecords, err := net.LookupMX(domain)
	if err != nil || len(mxRecords) == 0 {
		response.MXValid = false
		response.Error = "Domain does not have MX records"
		return response
	}
	response.MXValid = true

	return response
}

// handler 处理 HTTP 请求并返回验证结果
func Handler(w http.ResponseWriter, r *http.Request) {
	// 解析请求体
	var request EmailsRequest
	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}
	defer r.Body.Close()

	// 验证邮箱列表
	var results []EmailValidationResponse
	for _, email := range request.Emails {
		validationResult := validateEmail(email)
		results = append(results, validationResult)
	}

	// 返回验证结果
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}
