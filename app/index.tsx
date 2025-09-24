// app/index.tsx - BTEB Result App with Welcome Screen
import React, { useEffect, useState } from 'react';
import {
    ActivityIndicator,
    Alert,
    Image,
    SafeAreaView,
    ScrollView,
    StatusBar,
    StyleSheet,
    Text,
    TextInput,
    TouchableOpacity,
    View
} from 'react-native';
import * as Animatable from "react-native-animatable";
import AdMobBannerComponent from '../components/AdMobBanner';
import AdMobInterstitialComponent from '../components/AdMobInterstitial';
import { apiService } from '../services/apiService';

// Type definitions
interface SubjectResult {
  subjectCode: string;
  subjectName: string;
  failedType: string;
}

interface SemesterResult {
  publishedAt: string;
  semester: string;
  result: string | {
    failedList: SubjectResult[];
    passedList: SubjectResult[];
    gpa?: string;
    ref_subjects?: string[];
  };
  passed: boolean;
  gpa?: string;
}

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
  resultData: SemesterResult[];
}

interface Result {
  rollNo: string;
  regulation: string;
  program: string;
  instituteData: {
    code: string;
    name: string;
    district: string;
  };
  semesterResults: SemesterResult[];
  cgpaData?: Array<{
    semester: string;
    cgpa: string;
    publishedAt: string;
  }>;
}

// Constants
const REGULATIONS = ['2010', '2016', '2022']; // Will be updated dynamically from Firebase
const PROGRAMS = ['Diploma in Engineering'];

// GPA display function - shows exactly what API returns
const getSemesterGPA = (semesterResult: SemesterResult): string => {
  // If result is a GPA string, return it directly
  if (typeof semesterResult.result === 'string') {
    return semesterResult.result;
  }
  
  // If result is an object with subject lists, check if GPA is included
  if (typeof semesterResult.result === 'object' && semesterResult.result) {
    // Check if GPA is available in the result object
    if ('gpa' in semesterResult.result && semesterResult.result.gpa) {
      return semesterResult.result.gpa;
    }
    // Check if GPA is available in the semester result itself
    if (semesterResult.gpa) {
      return semesterResult.gpa;
    }
  }
  
  // If no GPA found, show "N/A"
  return 'N/A';
};

// Function to retrieve student information from API
const retrieveStudentInformation = async (
  studentIdentifier: string,
  academicPeriod: string,
  educationalProgram: string
): Promise<ApiResponse | null> => {
  return await apiService.fetchStudentData(studentIdentifier, academicPeriod, educationalProgram);
};

// Dropdown component
interface DropdownProps {
  options: string[];
  selectedValue: string | null;
  onValueChange: (value: string) => void;
  placeholder: string;
}

const Dropdown: React.FC<DropdownProps> = ({ options, selectedValue, onValueChange, placeholder }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <View style={styles.dropdownContainer}>
      <TouchableOpacity 
        style={styles.dropdownButton}
        onPress={() => setIsOpen(!isOpen)}
      >
        <Text style={styles.dropdownButtonText}>
          {selectedValue || placeholder}
        </Text>
        <Text style={styles.dropdownArrow}>{isOpen ? '▲' : '▼'}</Text>
      </TouchableOpacity>
      
      {isOpen && (
        <View style={styles.dropdownList}>
          {options.map((option) => (
            <TouchableOpacity 
              key={option}
              style={styles.dropdownItem}
              onPress={() => {
                onValueChange(option);
                setIsOpen(false);
              }}
            >
              <Text style={styles.dropdownItemText}>{option}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
};

export default function BTEBResultApp() {
  const [showWelcome, setShowWelcome] = useState(true);
  const [rollNo, setRollNo] = useState('');
  const [selectedRegulation, setSelectedRegulation] = useState<string | null>(null);
  const [selectedProgram, setSelectedProgram] = useState<string | null>('Diploma in Engineering');
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [availableRegulations, setAvailableRegulations] = useState<string[]>(REGULATIONS);

  // Welcome screen logic
  useEffect(() => {
    if (showWelcome) {
      const timer = setTimeout(() => {
        setShowWelcome(false);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [showWelcome]);

  // Load available regulations from API
  useEffect(() => {
    const loadRegulations = async () => {
      try {
        const response = await fetch('http://172.20.10.4:3001/api/regulations/Diploma%20in%20Engineering');
        const data = await response.json();
        
        if (data.success && data.regulations.length > 0) {
          setAvailableRegulations(data.regulations);
          console.log('✅ Loaded regulations from API:', data.regulations);
        } else {
          console.log('Using default regulations: 2010, 2016, 2022');
        }
      } catch (error) {
        console.log('Using default regulations due to API error:', error);
      }
    };
    
    loadRegulations();
  }, []);

  const handleSearch = async () => {
    if (!rollNo.trim()) {
      Alert.alert('Error', 'Please enter a roll number');
      return;
    }

    if (!selectedRegulation) {
      Alert.alert('Error', 'Please select a regulation');
      return;
    }

    if (!selectedProgram) {
      Alert.alert('Error', 'Please select a program');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const apiResponse = await retrieveStudentInformation(rollNo, selectedRegulation, selectedProgram);
      
      if (apiResponse && apiResponse.success) {
        // Use the data directly from API as it already has the correct structure
        const formattedResult: Result = {
          rollNo: apiResponse.roll,
          regulation: apiResponse.regulation,
          program: apiResponse.exam,
          instituteData: apiResponse.instituteData,
          semesterResults: apiResponse.resultData,
          cgpaData: apiResponse.cgpaData
        };
        setResult(formattedResult);
      } else {
        Alert.alert('Not Found', 'No result found for this roll number and regulation. Please verify your details and try again.');
        setResult(null);
      }
    } catch (error) {
      console.error('Search error:', error);
      
      // Check if it's a student not found error
      const errorMessage = error instanceof Error ? error.message : String(error);
      if (errorMessage.includes('Student not found')) {
        Alert.alert(
          'Student Not Found',
          'No result found for this roll number. Please verify the roll number and try again.\n\nTip: Try roll numbers like 190002, 189266, or 600070'
        );
      } else if (errorMessage.includes('Local database service unavailable')) {
        Alert.alert(
          'Service Unavailable',
          'The local database service is currently unavailable. Please make sure the API server is running.'
        );
      } else {
        Alert.alert(
          'Connection Error',
          'Unable to connect to the result server. Please check your internet connection and try again.'
        );
      }
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  // Welcome Screen Component
  if (showWelcome) {
    return (
      <View style={welcomeStyles.container}>
        {/* AdMob Interstitial Ad */}
        <AdMobInterstitialComponent
          adUnitId="ca-app-pub-8384502110540664/7094376320"
          onAdLoaded={() => console.log('Interstitial ad loaded')}
          onAdFailedToLoad={(error) => console.log('Interstitial ad failed:', error)}
          onAdOpened={() => console.log('Interstitial ad opened')}
          onAdClosed={() => console.log('Interstitial ad closed')}
        />
        
        {/* Logo with bounce animation */}
        <Animatable.View
          animation="bounceIn"
          duration={1500}
          delay={300}
          style={welcomeStyles.logoWrapper}
        >
          <Image 
            source={require('../assets/images/icon.png')} 
            style={welcomeStyles.logo}
            resizeMode="contain"
          />
        </Animatable.View>

        {/* Welcome Text with fade in animation */}
        <Animatable.Text
          animation="fadeInUp"
          duration={1000}
          delay={1000}
          style={welcomeStyles.title}
        >
          Welcome to BTEB Result
        </Animatable.Text>
        
        {/* Subtitle with pulse animation */}
        <Animatable.Text
          animation="pulse"
          iterationCount="infinite"
          duration={1500}
          delay={2000}
          style={welcomeStyles.subtitle}
        >
          Loading...
        </Animatable.Text>

        {/* Decorative dots */}
        <Animatable.View
          animation="fadeIn"
          duration={2000}
          delay={2500}
          style={welcomeStyles.dotsContainer}
        >
          <Animatable.View
            animation="bounce"
            iterationCount="infinite"
            duration={1000}
            style={[welcomeStyles.dot, welcomeStyles.dot1]}
          />
          <Animatable.View
            animation="bounce"
            iterationCount="infinite"
            duration={1000}
            delay={200}
            style={[welcomeStyles.dot, welcomeStyles.dot2]}
          />
          <Animatable.View
            animation="bounce"
            iterationCount="infinite"
            duration={1000}
            delay={400}
            style={[welcomeStyles.dot, welcomeStyles.dot3]}
          />
        </Animatable.View>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#ffffff" translucent={false} />
      
      <ScrollView style={styles.content}>
        <View style={styles.mainSearchContainer}>
          <Text style={styles.mainTitle}>Search Exam Results</Text>
          <Text style={styles.mainSubtitle}>Enter your roll number, select program and regulation to view results</Text>
          
          <View style={styles.searchInputContainer}>
            <View style={styles.programContainer}>
              <Text style={styles.programLabel}>Program:</Text>
              <Dropdown
                options={PROGRAMS}
                selectedValue={selectedProgram}
                onValueChange={setSelectedProgram}
                placeholder="Select Program"
              />
            </View>
            
            <TextInput
              style={styles.mainSearchInput}
              placeholder="Enter Roll Number (e.g., 721942)"
              value={rollNo}
              onChangeText={setRollNo}
              keyboardType="numeric"
              placeholderTextColor="#999"
            />
            
            <View style={styles.regulationContainer}>
              <Text style={styles.regulationLabel}>Regulation:</Text>
              <Dropdown
                options={availableRegulations}
                selectedValue={selectedRegulation}
                onValueChange={setSelectedRegulation}
                placeholder="Select Regulation"
              />
            </View>
          </View>

          <View style={styles.searchButtonContainer}>
            <TouchableOpacity 
              style={styles.mainSearchButton}
              onPress={handleSearch}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#ffffff" size="small" />
              ) : (
                <Text style={styles.mainSearchButtonText}>Search</Text>
              )}
            </TouchableOpacity>
          </View>

          {result && (
            <View style={styles.resultCard}>
              <View style={styles.resultHeader}>
                <Text style={styles.resultTitle}>Result Details</Text>
              </View>
              <View style={styles.resultDetails}>
                <View style={styles.resultRow}>
                  <Text style={styles.resultLabel}>Roll Number</Text>
                  <Text style={styles.resultValue}>{result.rollNo}</Text>
                </View>
                <View style={styles.resultRow}>
                  <Text style={styles.resultLabel}>Program</Text>
                  <Text style={styles.resultValue}>{result.program}</Text>
                </View>
                <View style={styles.resultRow}>
                  <Text style={styles.resultLabel}>Regulation</Text>
                  <Text style={styles.resultValue}>{result.regulation}</Text>
                </View>
                <View style={styles.resultRow}>
                  <Text style={styles.resultLabel}>Institute</Text>
                  <Text style={styles.resultValue}>{result.instituteData.name}</Text>
                </View>
                <View style={styles.resultRow}>
                  <Text style={styles.resultLabel}>Institute Code</Text>
                  <Text style={styles.resultValue}>{result.instituteData.code}</Text>
                </View>
                <View style={styles.resultRow}>
                  <Text style={styles.resultLabel}>District</Text>
                  <Text style={styles.resultValue}>{result.instituteData.district}</Text>
                </View>
              </View>
              
              {/* Semester Results */}
              <View style={styles.semesterResultsContainer}>
                <Text style={styles.semesterResultsTitle}>Semester Results</Text>
                {result.semesterResults.map((semesterResult, index) => (
                  <View key={index} style={styles.semesterCard}>
                    <View style={styles.semesterHeader}>
                      <Text style={styles.semesterTitle}>Semester {semesterResult.semester}</Text>
                      <Text style={[
                        styles.semesterStatus,
                        semesterResult.passed ? styles.passedStatus : styles.failedStatus
                      ]}>
                        {semesterResult.passed ? 'PASSED' : 'FAILED'}
                      </Text>
                    </View>
                    <View style={styles.semesterInfo}>
                      <Text style={styles.semesterDate}>
                        Published: {new Date(semesterResult.publishedAt).toLocaleDateString()}
                      </Text>
                      <Text style={styles.semesterGPA}>
                        GPA: {semesterResult.gpa || 'N/A'}
                      </Text>
                    </View>
                    
                    {typeof semesterResult.result === 'object' && semesterResult.result && (
                      <View style={styles.subjectResults}>
                        {/* Handle reference subjects for failed semesters */}
                        {semesterResult.gpa === "ref" && semesterResult.result.ref_subjects && semesterResult.result.ref_subjects.length > 0 && (
                          <View style={styles.subjectContainer}>
                            <Text style={styles.subjectListTitle}>Reference Subjects:</Text>
                            {semesterResult.result.ref_subjects.map((subject, subIndex) => (
                              <Text key={subIndex} style={styles.failedSubject}>
                                • {subject}
                              </Text>
                            ))}
                          </View>
                        )}
                        
                        {/* Handle traditional failed/passed lists if they exist */}
                        {semesterResult.result.failedList && semesterResult.result.failedList.length > 0 && (
                          <View style={styles.subjectContainer}>
                            <Text style={styles.subjectListTitle}>Failed Subjects:</Text>
                            {semesterResult.result.failedList.map((subject, subIndex) => (
                              <Text key={subIndex} style={styles.failedSubject}>
                                • {subject.subjectName} ({subject.subjectCode})
                              </Text>
                            ))}
                          </View>
                        )}
                        {semesterResult.result.passedList && semesterResult.result.passedList.length > 0 && (
                          <View style={styles.subjectContainer}>
                            <Text style={styles.subjectListTitle}>Passed Subjects:</Text>
                            {semesterResult.result.passedList.map((subject, subIndex) => (
                              <Text key={subIndex} style={styles.passedSubject}>
                                • {subject.subjectName} ({subject.subjectCode})
                              </Text>
                            ))}
                          </View>
                        )}
                        
                        {/* Show no data message if no subjects are available */}
                        {(!semesterResult.result.failedList || semesterResult.result.failedList.length === 0) && 
                         (!semesterResult.result.passedList || semesterResult.result.passedList.length === 0) &&
                         (!semesterResult.result.ref_subjects || semesterResult.result.ref_subjects.length === 0) && (
                          <View style={styles.subjectContainer}>
                            <Text style={styles.noDataText}>No subject details available</Text>
                          </View>
                        )}
                      </View>
                    )}
                  </View>
                ))}
              </View>
              
              {/* CGPA Results */}
              {result.cgpaData && result.cgpaData.length > 0 && (
                <View style={styles.cgpaResultsContainer}>
                  <Text style={styles.cgpaResultsTitle}>CGPA Results</Text>
                  {result.cgpaData.map((cgpaResult, index) => (
                    <View key={index} style={styles.cgpaCard}>
                      <View style={styles.cgpaHeader}>
                        <Text style={styles.cgpaTitle}>{cgpaResult.semester}</Text>
                        <Text style={styles.cgpaValue}>{cgpaResult.cgpa}</Text>
                      </View>
                      <Text style={styles.cgpaDate}>
                        Published: {new Date(cgpaResult.publishedAt).toLocaleDateString()}
                      </Text>
                    </View>
                  ))}
                </View>
              )}
            </View>
          )}
        </View>
        
        {/* AdMob Banner Ad */}
        <AdMobBannerComponent
          adUnitId="ca-app-pub-8384502110540664/7126698746"
          bannerSize="banner"
          style={styles.bannerAd}
        />
      </ScrollView>
    </SafeAreaView>
  );
}

// Styles
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
    paddingTop: 0,
  },
  content: {
    flex: 1,
  },
  mainSearchContainer: {
    backgroundColor: 'white',
    margin: 20,
    padding: 25,
    borderRadius: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  mainTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    color: '#333',
    marginBottom: 10,
  },
  mainSubtitle: {
    fontSize: 16,
    textAlign: 'center',
    color: '#666',
    marginBottom: 25,
    lineHeight: 22,
  },
  searchInputContainer: {
    marginBottom: 20,
  },
  programContainer: {
    marginBottom: 15,
  },
  programLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  regulationContainer: {
    marginBottom: 15,
  },
  regulationLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  mainSearchInput: {
    borderWidth: 2,
    borderColor: '#ddd',
    borderRadius: 12,
    padding: 15,
    fontSize: 16,
    backgroundColor: '#f9f9f9',
    marginBottom: 15,
  },
  searchButtonContainer: {
    alignItems: 'center',
    marginTop: 10,
  },
  mainSearchButton: {
    backgroundColor: '#333',
    paddingHorizontal: 40,
    paddingVertical: 15,
    borderRadius: 12,
    minWidth: 120,
    alignItems: 'center',
  },
  mainSearchButtonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  resultCard: {
    backgroundColor: '#f9f9f9',
    borderRadius: 12,
    padding: 20,
    marginTop: 20,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  resultHeader: {
    borderBottomWidth: 1,
    borderBottomColor: '#ddd',
    paddingBottom: 15,
    marginBottom: 15,
  },
  resultTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
  },
  resultDetails: {
    marginBottom: 20,
  },
  resultRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  resultLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#555',
    flex: 1,
  },
  resultValue: {
    fontSize: 16,
    color: '#333',
    flex: 2,
    textAlign: 'right',
  },
  dropdownContainer: {
    position: 'relative',
    zIndex: 1000,
  },
  dropdownButton: {
    borderWidth: 2,
    borderColor: '#ddd',
    borderRadius: 12,
    padding: 15,
    backgroundColor: '#f9f9f9',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  dropdownButtonText: {
    fontSize: 16,
    color: '#333',
  },
  dropdownArrow: {
    fontSize: 12,
    color: '#666',
  },
  dropdownList: {
    position: 'absolute',
    top: '100%',
    left: 0,
    right: 0,
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    marginTop: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    zIndex: 1001,
  },
  dropdownItem: {
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  dropdownItemText: {
    fontSize: 16,
    color: '#333',
  },
  semesterResultsContainer: {
    marginTop: 20,
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: '#ddd',
  },
  semesterResultsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  semesterCard: {
    backgroundColor: '#ffffff',
    borderRadius: 8,
    padding: 15,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  semesterHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  semesterTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  semesterStatus: {
    fontSize: 12,
    fontWeight: 'bold',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  passedStatus: {
    backgroundColor: '#d4edda',
    color: '#155724',
  },
  failedStatus: {
    backgroundColor: '#f8d7da',
    color: '#721c24',
  },
  semesterInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  semesterDate: {
    fontSize: 14,
    color: '#666',
  },
  semesterGPA: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#2E7D32',
  },
  subjectResults: {
    marginTop: 10,
  },
  subjectContainer: {
    marginBottom: 10,
  },
  subjectListTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  failedSubject: {
    fontSize: 13,
    color: '#721c24',
    marginLeft: 10,
    marginBottom: 2,
  },
  passedSubject: {
    fontSize: 13,
    color: '#155724',
    marginLeft: 10,
    marginBottom: 2,
  },
  noDataText: {
    fontSize: 13,
    color: '#666',
    fontStyle: 'italic',
    textAlign: 'center',
    marginTop: 10,
  },
  cgpaResultsContainer: {
    marginTop: 20,
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: '#ddd',
  },
  cgpaResultsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  cgpaCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 15,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  cgpaHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  cgpaTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  cgpaValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#28a745',
    backgroundColor: '#d4edda',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  cgpaDate: {
    fontSize: 12,
    color: '#666',
  },
  bannerAd: {
    marginHorizontal: 20,
    marginBottom: 20,
  },
});

// Welcome Screen Styles
const welcomeStyles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#ffffff",
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 20,
  },
  logoWrapper: {
    marginBottom: 50,
  },
  logo: {
    width: 180,
    height: 180,
  },
  title: {
    fontSize: 32,
    fontWeight: "700",
    color: "#000000",
    textAlign: "center",
    letterSpacing: 0.5,
    marginBottom: 20,
  },
  subtitle: {
    fontSize: 18,
    color: "#333333",
    textAlign: "center",
    fontWeight: "500",
    marginBottom: 60,
  },
  dotsContainer: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
  },
  dot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: "#000000",
    marginHorizontal: 8,
  },
  dot1: {
    backgroundColor: "#000000",
  },
  dot2: {
    backgroundColor: "#333333",
  },
  dot3: {
    backgroundColor: "#666666",
  },
});
