import React from "react";
import { Image, StyleSheet, View } from "react-native";
import * as Animatable from "react-native-animatable";
import AdMobInterstitialComponent from "../components/AdMobInterstitial";

export default function WelcomeScreen() {
  return (
    <View style={styles.container}>
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
        style={styles.logoWrapper}
      >
        <Image 
          source={require('../assets/images/icon.png')} 
          style={styles.logo}
          resizeMode="contain"
        />
      </Animatable.View>

      {/* Welcome Text with fade in animation */}
      <Animatable.Text
        animation="fadeInUp"
        duration={1000}
        delay={1000}
        style={styles.title}
      >
        Welcome to BTEB Result
      </Animatable.Text>
      
      {/* Subtitle with pulse animation */}
      <Animatable.Text
        animation="pulse"
        iterationCount="infinite"
        duration={1500}
        delay={2000}
        style={styles.subtitle}
      >
        Loading...
      </Animatable.Text>

      {/* Decorative dots */}
      <Animatable.View
        animation="fadeIn"
        duration={2000}
        delay={2500}
        style={styles.dotsContainer}
      >
        <Animatable.View
          animation="bounce"
          iterationCount="infinite"
          duration={1000}
          style={[styles.dot, styles.dot1]}
        />
        <Animatable.View
          animation="bounce"
          iterationCount="infinite"
          duration={1000}
          delay={200}
          style={[styles.dot, styles.dot2]}
        />
        <Animatable.View
          animation="bounce"
          iterationCount="infinite"
          duration={1000}
          delay={400}
          style={[styles.dot, styles.dot3]}
        />
      </Animatable.View>
    </View>
  );
}

const styles = StyleSheet.create({
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
