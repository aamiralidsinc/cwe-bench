package cwfunctional

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strconv"
	"strings"
	"testing"

	"github.com/QuantumNous/new-api/common"
	"github.com/QuantumNous/new-api/i18n"
	"github.com/QuantumNous/new-api/model"
	"github.com/QuantumNous/new-api/router"

	"github.com/gin-contrib/sessions"
	"github.com/gin-contrib/sessions/cookie"
	"github.com/gin-gonic/gin"
	"github.com/glebarez/sqlite"
	"gorm.io/gorm"
)

const (
	rootID   = 1
	adminID  = 2
	aliceID  = 3
	admin2ID = 4
	root2ID  = 5

	rootToken   = "cwb-root-token-0000000000000001"
	adminToken  = "cwb-admin-token-000000000000002"
	admin2Token = "cwb-admin2-token-000000000000003"
	aliceToken  = "cwb-alice-token-0000000000000004"

	rootWebhook = "cwb-root-webhook-signing-secret"
	rootGotify  = "cwb-root-gotify-app-token"
	rootBark    = "https://push.example.test/cwb-root-bark-device-key/push"

	adminWebhook = "cwb-admin-webhook-signing-secret"
	adminGotify  = "cwb-admin-gotify-app-token"

	aliceWebhook = "cwb-alice-webhook-signing-secret"
	aliceGotify  = "cwb-alice-gotify-app-token"
	aliceBark    = "https://push.example.test/cwb-alice-bark-device-key/push"

	rootAPIKey  = "sk-cwb-root-api-key-000000000001"
	adminAPIKey = "sk-cwb-admin-api-key-00000000002"
	aliceAPIKey = "sk-cwb-alice-api-key-00000000003"

	oauthProviderID = 1
)

func settingsBlob(webhook, gotify, bark, language string) string {
	return fmt.Sprintf(`{"webhook_secret":%q,"gotify_token":%q,"bark_url":%q,"webhook_url":"https://hooks.example.test/notify","gotify_url":"https://gotify.example.test","language":%q,"quota_warning_threshold":80}`,
		webhook, gotify, bark, language)
}

func newTestServer(t *testing.T) *gin.Engine {
	t.Helper()
	gin.SetMode(gin.TestMode)
	common.UsingSQLite = true
	common.UsingMySQL = false
	common.UsingPostgreSQL = false
	common.RedisEnabled = false
	common.DebugEnabled = false

	dsn := fmt.Sprintf("file:%s?mode=memory&cache=shared", strings.ReplaceAll(t.Name(), "/", "_"))
	db, err := gorm.Open(sqlite.Open(dsn), &gorm.Config{})
	if err != nil {
		t.Fatalf("open test database: %v", err)
	}
	model.DB = db
	model.LOG_DB = db
	if err := db.AutoMigrate(&model.User{}, &model.PasskeyCredential{}, &model.TwoFA{}, &model.TwoFABackupCode{}, &model.Token{}, &model.CustomOAuthProvider{}, &model.UserOAuthBinding{}); err != nil {
		t.Fatalf("migrate test database: %v", err)
	}
	if err := i18n.Init(); err != nil {
		t.Fatalf("initialize translations: %v", err)
	}

	engine := gin.New()
	engine.Use(sessions.Sessions("session", cookie.NewStore([]byte("cwbench-test-session"))))
	router.SetApiRouter(engine)
	return engine
}

func seedUser(t *testing.T, id int, username string, role int, token, setting string) {
	t.Helper()
	user := model.User{
		Id:          id,
		Username:    username,
		Password:    "test-password",
		DisplayName: username,
		Role:        role,
		Status:      common.UserStatusEnabled,
		Email:       username + "@example.test",
		Group:       "default",
		Quota:       1000,
		Setting:     setting,
		AffCode:     fmt.Sprintf("aff%08d", id),
	}
	if token != "" {
		user.SetAccessToken(token)
	}
	if err := model.DB.Create(&user).Error; err != nil {
		t.Fatalf("seed %s: %v", username, err)
	}
}

func seedUsers(t *testing.T) {
	t.Helper()
	seedUser(t, rootID, "root", common.RoleRootUser, rootToken, settingsBlob(rootWebhook, rootGotify, rootBark, "en"))
	seedUser(t, adminID, "admin", common.RoleAdminUser, adminToken, settingsBlob(adminWebhook, adminGotify, "", "zh"))
	seedUser(t, aliceID, "alice", common.RoleCommonUser, aliceToken, settingsBlob(aliceWebhook, aliceGotify, aliceBark, "zh"))
	seedUser(t, admin2ID, "admin2", common.RoleAdminUser, admin2Token, settingsBlob("", "", "", "en"))
}

func seedRoot2(t *testing.T) {
	t.Helper()
	seedUser(t, root2ID, "root2", common.RoleRootUser, "cwb-root2-token-000000000000005", "")
}

func seedToken(t *testing.T, id int, userID int, key, name string) {
	t.Helper()
	token := model.Token{
		Id:          id,
		UserId:      userID,
		Key:         key,
		Name:        name,
		Status:      1,
		CreatedTime: 1700000000,
		ExpiredTime: -1,
	}
	if err := model.DB.Create(&token).Error; err != nil {
		t.Fatalf("seed token: %v", err)
	}
}

func seedTokens(t *testing.T) {
	t.Helper()
	seedToken(t, 1, rootID, rootAPIKey, "root-api-key")
	seedToken(t, 2, adminID, adminAPIKey, "admin-api-key")
	seedToken(t, 3, aliceID, aliceAPIKey, "alice-api-key")
}

func seedOAuthProvider(t *testing.T) {
	t.Helper()
	provider := model.CustomOAuthProvider{
		Id:      oauthProviderID,
		Name:    "Test Sign-In Provider",
		Slug:    "test-sign-in",
		Enabled: true,
	}
	if err := model.DB.Create(&provider).Error; err != nil {
		t.Fatalf("seed sign-in provider: %v", err)
	}
}

func oauthBindingCount(t *testing.T, userID int) int64 {
	t.Helper()
	var count int64
	if err := model.DB.Model(&model.UserOAuthBinding{}).Where("user_id = ?", userID).Count(&count).Error; err != nil {
		t.Fatalf("count sign-in bindings: %v", err)
	}
	return count
}

type oauthBindingRequest struct {
	ProviderId     int    `json:"provider_id"`
	ProviderUserId string `json:"provider_user_id"`
}

func seedPasskey(t *testing.T, userID int) {
	t.Helper()
	credential := model.PasskeyCredential{
		UserID:       userID,
		CredentialID: fmt.Sprintf("cwb-credential-%d", userID),
		PublicKey:    "cwb-public-key",
	}
	if err := model.DB.Create(&credential).Error; err != nil {
		t.Fatalf("seed passkey: %v", err)
	}
}

func passkeyCount(t *testing.T, userID int) int64 {
	t.Helper()
	var count int64
	if err := model.DB.Model(&model.PasskeyCredential{}).Where("user_id = ?", userID).Count(&count).Error; err != nil {
		t.Fatalf("count passkeys: %v", err)
	}
	return count
}

func seedTwoFA(t *testing.T, userID int) {
	t.Helper()
	if err := model.DB.Create(&model.TwoFA{UserId: userID, Secret: "cwb-totp-secret", IsEnabled: true}).Error; err != nil {
		t.Fatalf("seed two-factor: %v", err)
	}
}

func twoFACount(t *testing.T, userID int) int64 {
	t.Helper()
	var count int64
	if err := model.DB.Model(&model.TwoFA{}).Where("user_id = ?", userID).Count(&count).Error; err != nil {
		t.Fatalf("count two-factor records: %v", err)
	}
	return count
}

func storedToken(t *testing.T, userID int) string {
	t.Helper()
	var user model.User
	if err := model.DB.First(&user, userID).Error; err != nil {
		t.Fatalf("load stored user: %v", err)
	}
	return user.GetAccessToken()
}

func request(t *testing.T, handler http.Handler, method, path, token string, userID int, body any) (int, []byte) {
	t.Helper()
	var payload []byte
	if body != nil {
		encoded, err := json.Marshal(body)
		if err != nil {
			t.Fatalf("encode request body: %v", err)
		}
		payload = encoded
	}
	req := httptest.NewRequest(method, path, bytes.NewReader(payload))
	if token != "" {
		req.Header.Set("Authorization", token)
		req.Header.Set("New-Api-User", strconv.Itoa(userID))
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	recorder := httptest.NewRecorder()
	handler.ServeHTTP(recorder, req)
	return recorder.Code, recorder.Body.Bytes()
}

func get(t *testing.T, handler http.Handler, path, token string, userID int) (int, []byte) {
	t.Helper()
	return request(t, handler, http.MethodGet, path, token, userID, nil)
}

func post(t *testing.T, handler http.Handler, path, token string, userID int, body any) (int, []byte) {
	t.Helper()
	return request(t, handler, http.MethodPost, path, token, userID, body)
}

func delete(t *testing.T, handler http.Handler, path, token string, userID int) (int, []byte) {
	t.Helper()
	return request(t, handler, http.MethodDelete, path, token, userID, nil)
}

type apiResponse struct {
	Success bool            `json:"success"`
	Message string          `json:"message"`
	Data    json.RawMessage `json:"data"`
}

func decodeResponse(t *testing.T, body []byte) apiResponse {
	t.Helper()
	var resp apiResponse
	if err := json.Unmarshal(body, &resp); err != nil {
		t.Fatalf("response is not the API envelope: %v", err)
	}
	return resp
}

func requireServed(t *testing.T, code int, body []byte) apiResponse {
	t.Helper()
	resp := decodeResponse(t, body)
	if code != http.StatusOK || !resp.Success {
		t.Fatalf("request was not served successfully: status %d", code)
	}
	return resp
}

func isRefusal(t *testing.T, code int, body []byte) bool {
	t.Helper()
	if code >= http.StatusInternalServerError {
		return false
	}
	if code >= http.StatusBadRequest {
		return true
	}
	return !decodeResponse(t, body).Success
}

func requireRefusal(t *testing.T, code int, body []byte, what string) {
	t.Helper()
	if !isRefusal(t, code, body) {
		t.Fatalf("%s was not refused (status %d)", what, code)
	}
}
