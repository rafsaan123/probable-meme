import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';

interface AdMobBannerProps {
  adUnitId: string;
  bannerSize?: 'banner' | 'largeBanner' | 'mediumRectangle' | 'fullBanner' | 'leaderboard' | 'smartBannerPortrait' | 'smartBannerLandscape';
  style?: any;
}

export default function AdMobBannerComponent({ 
  adUnitId, 
  bannerSize = 'banner',
  style 
}: AdMobBannerProps) {
  const [adLoaded, setAdLoaded] = useState(false);
  const [adError, setAdError] = useState(false);

  useEffect(() => {
    // Simulate ad loading
    const timer = setTimeout(() => {
      setAdLoaded(true);
      console.log('Banner ad loaded successfully:', adUnitId);
    }, 1000);

    return () => clearTimeout(timer);
  }, [adUnitId]);

  if (adError) {
    return (
      <View style={[styles.container, styles.errorContainer, style]}>
        <Text style={styles.errorText}>Ad failed to load</Text>
      </View>
    );
  }

  if (!adLoaded) {
    return (
      <View style={[styles.container, styles.loadingContainer, style]}>
        <Text style={styles.loadingText}>Loading ad...</Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, style]}>
      <TouchableOpacity 
        style={styles.adContainer}
        onPress={() => {
          console.log('Banner ad clicked:', adUnitId);
          // In production, this would open the ad
        }}
      >
        <Text style={styles.adText}>📱 Advertisement</Text>
        <Text style={styles.adSubtext}>Tap to learn more</Text>
        <Text style={styles.adUnitText}>{adUnitId}</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 10,
  },
  adContainer: {
    backgroundColor: '#4285f4',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 50,
    width: '100%',
    maxWidth: 320,
  },
  adText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  adSubtext: {
    color: '#ffffff',
    fontSize: 12,
    textAlign: 'center',
    marginTop: 4,
    opacity: 0.8,
  },
  adUnitText: {
    color: '#ffffff',
    fontSize: 8,
    textAlign: 'center',
    marginTop: 4,
    opacity: 0.6,
  },
  loadingContainer: {
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
    padding: 16,
    minHeight: 50,
    width: '100%',
    maxWidth: 320,
  },
  loadingText: {
    color: '#666',
    fontSize: 14,
    textAlign: 'center',
  },
  errorContainer: {
    backgroundColor: '#ffebee',
    borderRadius: 8,
    padding: 16,
    minHeight: 50,
    width: '100%',
    maxWidth: 320,
  },
  errorText: {
    color: '#c62828',
    fontSize: 14,
    textAlign: 'center',
  },
});
