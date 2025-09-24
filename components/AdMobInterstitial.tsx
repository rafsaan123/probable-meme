import { useEffect, useState } from 'react';
import { Alert } from 'react-native';

interface AdMobInterstitialProps {
  adUnitId: string;
  onAdLoaded?: () => void;
  onAdFailedToLoad?: (error: any) => void;
  onAdOpened?: () => void;
  onAdClosed?: () => void;
}

export default function AdMobInterstitialComponent({
  adUnitId,
  onAdLoaded,
  onAdFailedToLoad,
  onAdOpened,
  onAdClosed
}: AdMobInterstitialProps) {
  const [adLoaded, setAdLoaded] = useState(false);

  useEffect(() => {
    // Simulate ad loading
    const timer = setTimeout(() => {
      setAdLoaded(true);
      console.log('Interstitial ad loaded successfully:', adUnitId);
      onAdLoaded?.();
    }, 2000);

    return () => {
      clearTimeout(timer);
      console.log('Interstitial ad component cleaned up');
    };
  }, [adUnitId, onAdLoaded]);

  return null; // This component doesn't render anything
}

// Export the showAd function for use in other components
export const showInterstitialAd = async () => {
  try {
    console.log('Showing interstitial ad...');
    
    // Simulate showing an interstitial ad
    Alert.alert(
      'Advertisement',
      'This would be an interstitial ad in production.',
      [
        {
          text: 'Close',
          onPress: () => {
            console.log('Interstitial ad closed');
          }
        }
      ]
    );
    
    return Promise.resolve();
  } catch (error) {
    console.log('Error showing interstitial ad:', error);
  }
};
