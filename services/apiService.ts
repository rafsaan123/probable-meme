// API Service for BTEB Results App - Firebase Enterprise Integration
interface ApiResponse {
  success: boolean;
  time: string;
  roll: string;
  regulation: string;
  exam: string;
  instituteData: {
    code: string;
    name: string;
    district: string;
  };
  resultData: Array<{
    publishedAt: string;
    semester: string;
    result: string | {
      failedList: Array<{
        subjectCode: string;
        subjectName: string;
        failedType: string;
      }>;
      passedList: Array<{
        subjectCode: string;
        subjectName: string;
        failedType: string;
      }>;
      gpa?: string;
    };
    passed: boolean;
    gpa?: string;
  }>;
  cgpaData?: Array<{
    semester: string;
    cgpa: string;
    publishedAt: string;
  }>;
}

// Configuration
const API_ENDPOINT = '/api/search-result';

// Supabase API server (serves Supabase database with comprehensive BTEB data)
// Use local server for now (Vercel deployment has issues)
const SUPABASE_API = 'http://172.20.10.4:3001';

// Obfuscated function names to hide API calls
const obfuscatedFetch = async (url: string, options: any): Promise<Response> => {
  return fetch(url, options);
};

const obfuscatedJsonParse = (response: Response): Promise<any> => {
  return response.json();
};

// Firebase API integration only

// Main API service class
export class ApiService {
  private static instance: ApiService;
  
  private constructor() {}
  
  public static getInstance(): ApiService {
    if (!ApiService.instance) {
      ApiService.instance = new ApiService();
    }
    return ApiService.instance;
  }
  
  // Obfuscated method name to hide the actual API call
  public async fetchStudentData(
    studentId: string,
    academicYear: string,
    programType: string
  ): Promise<ApiResponse | null> {
    try {
      // Validate inputs
      if (!studentId || !academicYear || !programType) {
        throw new Error('Missing required parameters');
      }
      
      // Fetch data from Firebase API server
      const requestData = {
        rollNo: studentId,
        regulation: academicYear,
        program: programType
      };
      
      const response = await obfuscatedFetch(`${SUPABASE_API}${API_ENDPOINT}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'User-Agent': 'BTEB-Result-Mobile/1.0',
        },
        body: JSON.stringify(requestData),
      });
      
      if (response.ok) {
        const data = await obfuscatedJsonParse(response);
        if (data.success) {
          console.log('✅ Successfully fetched data via Supabase API');
          return data as ApiResponse;
        } else {
          throw new Error(data.error || 'API returned unsuccessful response');
        }
      } else if (response.status === 404) {
        // Student not found - this is a valid response, not an error
        const data = await obfuscatedJsonParse(response);
        throw new Error(data.error || 'Student not found');
      } else {
        throw new Error(`API request failed with status: ${response.status}`);
      }
      
    } catch (error) {
      console.error('API Service Error:', error);
      return null;
    }
  }
  
  // Health check method for Supabase API
  public async checkServiceHealth(): Promise<boolean> {
    try {
      const response = await obfuscatedFetch(`${SUPABASE_API}/health`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });
      
      return response.ok;
    } catch (error) {
      console.error('Supabase API health check failed:', error);
      return false;
    }
  }
}

// Export singleton instance
export const apiService = ApiService.getInstance();
