<template>
  <div class="admin-settings">
    <v-container>
      <v-row>
        <v-col cols="12">
          <v-card>
            <v-card-title class="headline">
              <v-icon large left class="mr-2">mdi-cog</v-icon>
              Admin Settings
            </v-card-title>
          </v-card>
        </v-col>
      </v-row>

      <!-- Loading indicator -->
      <v-row v-if="loading">
        <v-col cols="12" class="text-center">
          <v-progress-circular
            indeterminate
            color="primary"
            size="64"
          ></v-progress-circular>
          <p class="mt-3">Loading settings...</p>
        </v-col>
      </v-row>

      <!-- Error state -->
      <v-row v-else-if="error">
        <v-col cols="12">
          <v-alert
            type="error"
            border="left"
            class="mb-3"
          >
            {{ error }}
            <v-btn
              text
              small
              color="error"
              class="ml-2"
              @click="loadSettings"
            >
              Retry
            </v-btn>
          </v-alert>
        </v-col>
      </v-row>

      <!-- Settings content -->
      <template v-else>
        <!-- Settings navigation -->
        <v-row>
          <v-col cols="12" md="3">
            <v-card>
              <v-list rounded>
                <v-list-item-group
                  v-model="activeCategory"
                  color="primary"
                >
                  <v-list-item
                    v-for="(category, index) in Object.keys(settingsByCategory)"
                    :key="index"
                    :value="category"
                  >
                    <v-list-item-icon>
                      <v-icon>{{ getCategoryIcon(category) }}</v-icon>
                    </v-list-item-icon>
                    <v-list-item-content>
                      <v-list-item-title>{{ formatCategoryName(category) }}</v-list-item-title>
                    </v-list-item-content>
                  </v-list-item>
                </v-list-item-group>
              </v-list>

              <v-divider></v-divider>
              
              <v-card-actions>
                <v-btn
                  color="primary"
                  block
                  @click="initializeDefaultSettings"
                  :loading="initializingDefaults"
                >
                  <v-icon left>mdi-restore</v-icon>
                  Reset to Defaults
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-col>

          <!-- Settings form -->
          <v-col cols="12" md="9">
            <v-card v-if="activeCategory && settingsByCategory[activeCategory]">
              <v-card-title class="headline">
                {{ formatCategoryName(activeCategory) }} Settings
              </v-card-title>

              <v-card-text>
                <v-form ref="settingsForm" v-model="formValid">
                  <v-row>
                    <v-col
                      cols="12"
                      v-for="setting in settingsByCategory[activeCategory]"
                      :key="setting.id"
                    >
                      <!-- String setting -->
                      <v-text-field
                        v-if="setting.value_type === 'string'"
                        v-model="settingValues[setting.key]"
                        :label="setting.description || formatSettingKey(setting.key)"
                        :hint="getSettingHint(setting)"
                        :type="setting.is_sensitive ? 'password' : 'text'"
                        :required="setting.is_required"
                        :error-messages="getValidationError(setting.key)"
                        persistent-hint
                        @input="validateSetting(setting.key)"
                      ></v-text-field>

                      <!-- Number setting -->
                      <v-text-field
                        v-else-if="setting.value_type === 'number'"
                        v-model.number="settingValues[setting.key]"
                        :label="setting.description || formatSettingKey(setting.key)"
                        :hint="getSettingHint(setting)"
                        type="number"
                        :required="setting.is_required"
                        :error-messages="getValidationError(setting.key)"
                        persistent-hint
                        @input="validateSetting(setting.key)"
                      ></v-text-field>

                      <!-- Boolean setting -->
                      <v-switch
                        v-else-if="setting.value_type === 'boolean'"
                        v-model="settingValues[setting.key]"
                        :label="setting.description || formatSettingKey(setting.key)"
                        :hint="getSettingHint(setting)"
                        :error-messages="getValidationError(setting.key)"
                        persistent-hint
                      ></v-switch>

                      <!-- JSON setting (advanced) -->
                      <v-textarea
                        v-else-if="setting.value_type === 'json'"
                        v-model="settingValues[setting.key]"
                        :label="setting.description || formatSettingKey(setting.key)"
                        :hint="getSettingHint(setting)"
                        :required="setting.is_required"
                        :error-messages="getValidationError(setting.key)"
                        persistent-hint
                        rows="4"
                        @input="validateJsonSetting(setting.key)"
                      ></v-textarea>
                    </v-col>
                  </v-row>
                </v-form>
              </v-card-text>

              <v-divider></v-divider>

              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn
                  color="primary"
                  @click="saveSettings"
                  :loading="saving"
                  :disabled="!formValid || !hasChanges"
                >
                  <v-icon left>mdi-content-save</v-icon>
                  Save Changes
                </v-btn>
              </v-card-actions>

              <!-- Snackbar for notifications -->
              <v-snackbar
                v-model="snackbar.show"
                :color="snackbar.color"
                :timeout="snackbar.timeout"
              >
                {{ snackbar.text }}
                <template v-slot:action="{ attrs }">
                  <v-btn
                    text
                    v-bind="attrs"
                    @click="snackbar.show = false"
                  >
                    Close
                  </v-btn>
                </template>
              </v-snackbar>
            </v-card>
          </v-col>
        </v-row>
      </template>
    </v-container>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { adminSettingsApi } from '@/api/api';

export default {
  name: 'AdminSettings',
  
  setup() {
    // State
    const loading = ref(true);
    const error = ref(null);
    const originalSettings = ref([]);
    const settingsByCategory = ref({});
    const activeCategory = ref(null);
    const settingValues = reactive({});
    const validationErrors = reactive({});
    const formValid = ref(true);
    const saving = ref(false);
    const initializingDefaults = ref(false);
    const settingsForm = ref(null);
    
    const snackbar = reactive({
      show: false,
      text: '',
      color: 'success',
      timeout: 3000
    });

    // Category icons mapping
    const categoryIcons = {
      security: 'mdi-shield-lock',
      system: 'mdi-server',
      notification: 'mdi-bell',
      default: 'mdi-cog'
    };

    // Computed properties
    const hasChanges = computed(() => {
      for (const setting of originalSettings.value) {
        const currentValue = settingValues[setting.key];
        
        // Handle JSON strings
        if (setting.value_type === 'json' && typeof currentValue === 'string') {
          try {
            const parsedCurrent = JSON.parse(currentValue);
            const parsedOriginal = typeof setting.value === 'string' 
              ? JSON.parse(setting.value) 
              : setting.value;
            
            if (JSON.stringify(parsedCurrent) !== JSON.stringify(parsedOriginal)) {
              return true;
            }
          } catch (e) {
            // If we can't parse, consider it changed
            return true;
          }
        } 
        // Handle other types
        else if (currentValue !== setting.value) {
          return true;
        }
      }
      return false;
    });

    // Methods
    const loadSettings = async () => {
      loading.value = true;
      error.value = null;
      
      try {
        const response = await adminSettingsApi.getSettingsByCategory();
        
        // Store original settings
        const allSettings = [];
        for (const category in response) {
          if (response[category]) {
            allSettings.push(...response[category]);
          }
        }
        originalSettings.value = allSettings;
        
        // Group settings by category
        settingsByCategory.value = response;
        
        // Set active category to the first one if not already set
        if (!activeCategory.value && Object.keys(response).length > 0) {
          activeCategory.value = Object.keys(response)[0];
        }
        
        // Populate setting values
        populateSettingValues();
        
      } catch (err) {
        console.error('Error loading settings:', err);
        error.value = 'Failed to load settings. Please try again.';
      } finally {
        loading.value = false;
      }
    };

    const populateSettingValues = () => {
      // Reset any existing values
      Object.keys(settingValues).forEach(key => {
        delete settingValues[key];
      });
      
      // Set values from original settings
      originalSettings.value.forEach(setting => {
        // For JSON type, convert to string for editing if it's an object
        if (setting.value_type === 'json' && typeof setting.value === 'object') {
          settingValues[setting.key] = JSON.stringify(setting.value, null, 2);
        } else {
          settingValues[setting.key] = setting.value;
        }
      });
    };

    const validateSetting = (key) => {
      const setting = originalSettings.value.find(s => s.key === key);
      
      if (!setting) return;
      
      // Clear previous error
      delete validationErrors[key];
      
      const value = settingValues[key];
      
      // Required check
      if (setting.is_required && (value === null || value === undefined || value === '')) {
        validationErrors[key] = 'This field is required';
        return false;
      }
      
      // Type validation
      if (setting.value_type === 'number' && isNaN(Number(value))) {
        validationErrors[key] = 'Must be a valid number';
        return false;
      }
      
      return true;
    };

    const validateJsonSetting = (key) => {
      const setting = originalSettings.value.find(s => s.key === key);
      
      if (!setting) return;
      
      // Clear previous error
      delete validationErrors[key];
      
      const value = settingValues[key];
      
      // Required check
      if (setting.is_required && !value) {
        validationErrors[key] = 'This field is required';
        return false;
      }
      
      // JSON validation
      if (value) {
        try {
          JSON.parse(value);
        } catch (e) {
          validationErrors[key] = 'Invalid JSON format';
          return false;
        }
      }
      
      return true;
    };

    const validateAllSettings = () => {
      // Reset validation
      Object.keys(validationErrors).forEach(key => {
        delete validationErrors[key];
      });
      
      let isValid = true;
      
      // Validate each setting
      for (const setting of originalSettings.value) {
        if (setting.value_type === 'json') {
          if (!validateJsonSetting(setting.key)) {
            isValid = false;
          }
        } else {
          if (!validateSetting(setting.key)) {
            isValid = false;
          }
        }
      }
      
      return isValid;
    };

    const saveSettings = async () => {
      // Validate all settings
      if (!validateAllSettings()) {
        showSnackbar('Please correct the validation errors', 'error');
        return;
      }
      
      saving.value = true;
      
      try {
        // Find changed settings
        const changedSettings = originalSettings.value.filter(setting => {
          if (setting.value_type === 'json' && typeof settingValues[setting.key] === 'string') {
            try {
              const parsedValue = JSON.parse(settingValues[setting.key]);
              return JSON.stringify(parsedValue) !== JSON.stringify(setting.value);
            } catch (e) {
              // If we can't parse, consider it changed
              return true;
            }
          } else {
            return settingValues[setting.key] !== setting.value;
          }
        });
        
        // Update each changed setting
        const updatePromises = changedSettings.map(setting => {
          let value = settingValues[setting.key];
          
          // Parse JSON string to object
          if (setting.value_type === 'json' && typeof value === 'string') {
            try {
              value = JSON.parse(value);
            } catch (e) {
              throw new Error(`Invalid JSON format for setting ${setting.key}`);
            }
          }
          
          return adminSettingsApi.updateSettingValue(setting.key, { value });
        });
        
        await Promise.all(updatePromises);
        
        // Reload settings to get updated values
        await loadSettings();
        
        showSnackbar('Settings saved successfully', 'success');
      } catch (err) {
        console.error('Error saving settings:', err);
        showSnackbar('Failed to save settings', 'error');
      } finally {
        saving.value = false;
      }
    };

    const initializeDefaultSettings = async () => {
      if (!confirm('This will reset all settings to their default values. Continue?')) {
        return;
      }
      
      initializingDefaults.value = true;
      
      try {
        await adminSettingsApi.initializeDefaultSettings();
        await loadSettings();
        showSnackbar('Settings reset to defaults', 'success');
      } catch (err) {
        console.error('Error resetting settings:', err);
        showSnackbar('Failed to reset settings', 'error');
      } finally {
        initializingDefaults.value = false;
      }
    };

    const showSnackbar = (text, color = 'success') => {
      snackbar.text = text;
      snackbar.color = color;
      snackbar.show = true;
    };

    const formatCategoryName = (category) => {
      return category.charAt(0).toUpperCase() + category.slice(1);
    };

    const formatSettingKey = (key) => {
      // Extract the last part of the key (after the last dot)
      const parts = key.split('.');
      const lastPart = parts[parts.length - 1];
      
      // Convert camelCase or snake_case to readable format
      return lastPart
        .replace(/_/g, ' ')
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, str => str.toUpperCase());
    };

    const getCategoryIcon = (category) => {
      return categoryIcons[category] || categoryIcons.default;
    };

    const getSettingHint = (setting) => {
      let hint = '';
      
      if (setting.is_required) {
        hint += 'Required. ';
      }
      
      if (setting.is_sensitive) {
        hint += 'Contains sensitive information. ';
      }
      
      if (setting.value_type === 'json') {
        hint += 'Enter valid JSON. ';
      }
      
      return hint || null;
    };

    const getValidationError = (key) => {
      return validationErrors[key] || null;
    };

    // Lifecycle hooks
    onMounted(() => {
      loadSettings();
    });

    return {
      loading,
      error,
      settingsByCategory,
      activeCategory,
      settingValues,
      formValid,
      saving,
      initializingDefaults,
      snackbar,
      hasChanges,
      settingsForm,
      loadSettings,
      saveSettings,
      initializeDefaultSettings,
      formatCategoryName,
      formatSettingKey,
      getCategoryIcon,
      getSettingHint,
      getValidationError,
      validateSetting,
      validateJsonSetting
    };
  }
};
</script>

<style scoped>
.admin-settings {
  margin-bottom: 40px;
}
</style> 